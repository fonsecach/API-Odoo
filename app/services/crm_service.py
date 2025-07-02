
import logging
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

# Importa as configurações de conexão do Odoo
from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import OpportunityCreateIntelligent, OpportunityPowerBIData

# Importa a classe AsyncOdooClient
from app.services.async_odoo_client import AsyncOdooClient
from app.services.company_service import get_or_create_partner_by_vat

logger = logging.getLogger(__name__)  # Mantenha apenas uma atribuição para o logger


# Definição da função get_odoo_client que estava faltando neste arquivo
async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


# --- Funções síncronas existentes ---
def get_opportunities_info(models, db, uid, password, limit=100, offset=0):
    try:
        opportunities_info = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'search_read',
            [[]],
            {'limit': limit, 'offset': offset},
        )
        return opportunities_info
    except Exception as e:
        # Para consistência e melhor depuração, considere usar logger.error aqui também
        print(f'Erro ao buscar e ler informações das oportunidades: {e}')
        return []


def fetch_opportunity_by_id(models, db, uid, password, opportunity_id):
    try:
        opportunities_info = models.execute_kw(
            db, uid, password, 'crm.lead', 'read', [opportunity_id]
        )
        return opportunities_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações da oportunidade: {e}')
        return []


def create_opportunity_in_crm(opportunity_info, models, db, uid, password):
    try:
        return models.execute_kw(
            db, uid, password, 'crm.lead', 'create', [opportunity_info]
        )
    except Exception as e:
        # Considere loggar o erro antes de levantar a HTTPException
        logger.error(f"Erro ao criar oportunidade síncrona: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar oportunidade: {str(e)}',
        )


# --- Função assíncrona para criação inteligente ---
async def create_opportunity_intelligent_async(
    opportunity_payload: OpportunityCreateIntelligent
) -> Optional[Dict[str, Any]]:
    """
    Cria uma oportunidade de forma inteligente:
    1. Verifica/Cria a empresa associada pelo CNPJ.
    2. Cria a oportunidade no Odoo associada a essa empresa.
    Args:
        opportunity_payload: Dados da oportunidade e da empresa.
    Returns:
        Um dicionário com os detalhes da oportunidade criada, ou levanta HTTPException em caso de erro.
    Raises:
        HTTPException: Em caso de erros específicos (ex: falha ao obter/criar parceiro, erro no Odoo).
    """
    # Agora esta chamada funcionará, pois get_odoo_client() está definido acima neste arquivo.
    odoo_async_client = await get_odoo_client()

    # Passo 1: Obter ou criar o parceiro (empresa)
    try:
        partner_id = await get_or_create_partner_by_vat(
            vat_number=opportunity_payload.company_vat,
            company_name=opportunity_payload.company_name
        )
    except ValueError as ve:  # Erro de validação do VAT (ex: CNPJ inválido)
        logger.error(f"ValueError ao obter/criar parceiro para VAT {opportunity_payload.company_vat}: {str(ve)}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(ve))
    except Exception as e_partner:  # Outros erros ao obter/criar parceiro
        logger.exception(f"Erro inesperado ao obter/criar parceiro para VAT {opportunity_payload.company_vat}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar dados da empresa: {str(e_partner)}"
        )

    if not partner_id:  # Se get_or_create_partner_by_vat retornar None (apesar de agora levantar exceção)
        logger.error(f"Não foi possível obter ou criar o parceiro (ID nulo retornado) para VAT {opportunity_payload.company_vat} e nome {opportunity_payload.company_name}.")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,  # Ou 500 se for uma falha inesperada do serviço de empresa
            detail=f"Falha ao processar dados da empresa para VAT: {opportunity_payload.company_vat}"
        )

    # Passo 2: Preparar dados da oportunidade para o Odoo
    opportunity_data_odoo = {
        'name': opportunity_payload.name,
        'partner_id': partner_id,
        'user_id': opportunity_payload.user_id,
        'team_id': opportunity_payload.team_id,  # Se opcional e None, será removido abaixo
        'stage_id': opportunity_payload.stage_id,  # Se opcional e None, será removido abaixo
        'type': 'opportunity',
        # Odoo pode interpretar False como "não definido" ou um valor booleano literal.
        # Se o campo x_studio_tese for um campo de texto, enviar False pode não ser o ideal.
        # Enviar o valor original ou omitir se None.
        'x_studio_tese': opportunity_payload.x_studio_tese,
        'expected_revenue': opportunity_payload.expected_revenue,
    }
    # Remove chaves com valor None para que Odoo use seus padrões, se houver.
    opportunity_data_odoo = {k: v for k, v in opportunity_data_odoo.items() if v is not None}

    # Passo 3: Criar a oportunidade no CRM usando AsyncOdooClient
    try:
        opportunity_id = await odoo_async_client.create('crm.lead', opportunity_data_odoo)

        if not opportunity_id:  # Checagem caso o Odoo retorne algo falsy sem erro
            logger.error(f"Falha ao criar oportunidade '{opportunity_payload.name}' no Odoo (nenhum ID retornado).")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="O Odoo não retornou um ID para a oportunidade criada."
            )

        logger.info(f"Oportunidade '{opportunity_payload.name}' criada com sucesso, ID: {opportunity_id}.")

        # Passo 4: Ler os dados da oportunidade criada para retornar
        fields_to_read = ['name', 'partner_id', 'x_studio_tese', 'user_id', 'team_id', 'stage_id', 'expected_revenue']
        created_opportunity_data_list = await odoo_async_client.search_read(
            'crm.lead',
            [['id', '=', opportunity_id]],
            fields=fields_to_read
        )

        if not created_opportunity_data_list:
            logger.error(f"Oportunidade ID {opportunity_id} criada, mas falha ao reler os dados.")
            # É crítico não conseguir reler, pode indicar um problema.
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Falha ao obter detalhes da oportunidade recém-criada."
            )

        details = created_opportunity_data_list[0]

        # Função auxiliar para extrair ID de campos relacionais [ID, "Nome"] ou retornar o valor se já for ID
        def get_id_from_relational(field_value, fallback_id=None):
            if isinstance(field_value, list) and field_value:
                return field_value[0]
            # Se o Odoo não retornar o campo (ex: se era opcional e não foi setado),
            # podemos usar o fallback_id que veio do payload original (se aplicável e desejado)
            # ou deixar como None se o schema de retorno permitir.
            return fallback_id if field_value is False or field_value is None else field_value

        return_data = {
            "opportunity_id": opportunity_id,
            "name": details.get('name'),
            "partner_id": get_id_from_relational(details.get('partner_id'), partner_id),  # partner_id é o ID que já temos
            "x_studio_tese": details.get('x_studio_tese') if details.get('x_studio_tese') is not False else None,
            "user_id": get_id_from_relational(details.get('user_id'), opportunity_payload.user_id),
            "team_id": get_id_from_relational(details.get('team_id'), opportunity_payload.team_id),
            "stage_id": get_id_from_relational(details.get('stage_id'), opportunity_payload.stage_id),
            "expected_revenue": details.get('expected_revenue'),
        }
        return return_data

    except HTTPException:  # Re-levanta HTTPExceptions já tratadas (ex: de get_or_create_partner_by_vat)
        raise
    except Exception as e:  # Captura outras exceções da interação com Odoo (create, search_read)
        logger.exception(f"Exceção ao interagir com Odoo para oportunidade '{opportunity_payload.name}'")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao interagir com o Odoo para criar/ler oportunidade: {str(e)}"
        )


async def fetch_opportunities_for_powerbi_by_company(company_id: int) -> List[OpportunityPowerBIData]:
    """
    Busca oportunidades do CRM filtradas por ID da empresa para PowerBI.
    
    Args:
        company_id: ID da empresa (partner_id) para filtrar as oportunidades.
    
    Returns:
        Lista de OpportunityPowerBIData filtradas pela empresa especificada.
    """
    try:
        odoo_client = await get_odoo_client()
        
        fields_to_fetch = [
            'id', 'create_date', 'name', 'x_studio_tese', 'partner_id',
            'user_id', 'team_id', 'activity_ids', 'expected_revenue', 'probability',
            'stage_id', 'active', 'won_status', 'lost_reason_id', 'state_id',
            'phone', 'email_from', 'street', 'city', 'zip', 'country_id',
            'x_studio_previsao_inss', 'x_studio_previsao_ipi', 
            'x_studio_previsao_irpj_e_csll', 'x_studio_previsao_pis_e_cofins',
            'x_studio_debitos', 'x_studio_ultima_atualizacao_de_estagio',
            'x_studio_ticket_de_1_anlise', 'x_studio_ticket_de_2_analise',
            'x_studio_probabilidade', 'x_studio_receita_bruta_esperada',
            'x_studio_faturamento_esperado', 'x_studio_honorrios_1',
            'write_date', 'date_closed', 'x_studio_tipo_de_oportunidade_1',
            'x_studio_data_calculo_pendente', 'x_studio_data_em_processamento_1',
            'x_studio_data_calculo_concluido', 'x_studio_usuario_calculo_concluido'
        ]
        
        # Filter opportunities by partner_id (company_id)
        domain = [['partner_id', '=', company_id]]
        
        opportunities_data = await odoo_client.search_read(
            'crm.lead',
            domain=domain,
            fields=fields_to_fetch
        )
        
        if not opportunities_data:
            logger.info(f"Nenhuma oportunidade encontrada para a empresa ID {company_id}")
            return []
        
        processed_opportunities = []
        
        for opp_data in opportunities_data:
            try:
                # Get field descriptions for selection fields
                x_studio_tese_desc = await _get_selection_field_description(
                    odoo_client, 'crm.lead', 'x_studio_tese', opp_data.get('x_studio_tese')
                )
                
                processed_opp = {
                    'id': opp_data.get('id'),
                    'create_date': opp_data.get('create_date'),
                    'name': opp_data.get('name'),
                    'x_studio_tese': x_studio_tese_desc,
                    'partner_id': _extract_relational_name(opp_data.get('partner_id')),
                    'user_id': _extract_relational_name(opp_data.get('user_id')),
                    'team_id': _extract_relational_name(opp_data.get('team_id')),
                    'activity_ids': _format_activity_ids(opp_data.get('activity_ids')),
                    'expected_revenue': opp_data.get('expected_revenue'),
                    'probability': opp_data.get('probability'),
                    'stage_id': _extract_relational_name(opp_data.get('stage_id')),
                    'state_id': _extract_relational_name(opp_data.get('state_id')),
                    'active': opp_data.get('active'),
                    'won_status': opp_data.get('won_status'),
                    'lost_reason_id': _extract_relational_name(opp_data.get('lost_reason_id')),
                    'phone': opp_data.get('phone'),
                    'email_from': opp_data.get('email_from'),
                    'street': opp_data.get('street'),
                    'city': opp_data.get('city'),
                    'zip': opp_data.get('zip'),
                    'country_id': _extract_relational_name(opp_data.get('country_id')),
                    'x_studio_previsao_inss': opp_data.get('x_studio_previsao_inss'),
                    'x_studio_previsao_ipi': opp_data.get('x_studio_previsao_ipi'),
                    'x_studio_previsao_irpj_e_csll': opp_data.get('x_studio_previsao_irpj_e_csll'),
                    'x_studio_previsao_pis_e_cofins': opp_data.get('x_studio_previsao_pis_e_cofins'),
                    'x_studio_debitos': opp_data.get('x_studio_debitos'),
                    'x_studio_ultima_atualizacao_de_estagio': opp_data.get('x_studio_ultima_atualizacao_de_estagio'),
                    'x_studio_ticket_de_1_anlise': opp_data.get('x_studio_ticket_de_1_anlise'),
                    'x_studio_ticket_de_2_analise': opp_data.get('x_studio_ticket_de_2_analise'),
                    'x_studio_probabilidade': opp_data.get('x_studio_probabilidade'),
                    'x_studio_receita_bruta_esperada': opp_data.get('x_studio_receita_bruta_esperada'),
                    'x_studio_faturamento_esperado': opp_data.get('x_studio_faturamento_esperado'),
                    'x_studio_honorrios_1': opp_data.get('x_studio_honorrios_1'),
                    'write_date': opp_data.get('write_date'),
                    'date_closed': opp_data.get('date_closed'),
                    'x_studio_tipo_de_oportunidade_1': opp_data.get('x_studio_tipo_de_oportunidade_1'),
                    'x_studio_data_calculo_pendente': opp_data.get('x_studio_data_calculo_pendente'),
                    'x_studio_data_em_processamento_1': opp_data.get('x_studio_data_em_processamento_1'),
                    'x_studio_data_calculo_concluido': opp_data.get('x_studio_data_calculo_concluido'),
                    'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido'))
                }
                
                # Get additional partner data if needed
                partner_id = _extract_relational_id(opp_data.get('partner_id'))
                if partner_id:
                    try:
                        partner_data = await odoo_client.search_read(
                            'res.partner',
                            domain=[['id', '=', partner_id]],
                            fields=['x_studio_categoria_economica']
                        )
                        
                        if partner_data:
                            partner_info = partner_data[0]
                            # Get categoria economica description
                            categoria_desc = await _get_selection_field_description(
                                odoo_client, 'res.partner', 'x_studio_categoria_economica', 
                                partner_info.get('x_studio_categoria_economica')
                            )
                            processed_opp['x_studio_categoria_economica'] = categoria_desc
                    except Exception as partner_error:
                        logger.warning(f"Erro ao buscar dados do parceiro {partner_id}: {str(partner_error)}")
                        processed_opp['x_studio_categoria_economica'] = None
                else:
                    processed_opp['x_studio_categoria_economica'] = None
                
                # Get stage tracking data from mail.message
                try:
                    tracking_data = await get_opportunity_stage_tracking_data(opp_data.get('id'))
                    processed_opp.update({
                        'stage_tracking_calculo_pendente_date': tracking_data.get('calculo_pendente_date'),
                        'stage_tracking_em_processamento_date': tracking_data.get('em_processamento_date'),
                        'stage_tracking_calculo_concluido_date': tracking_data.get('calculo_concluido_date'),
                        'stage_tracking_calculo_pendente_user': tracking_data.get('calculo_pendente_user')
                    })
                except Exception as tracking_error:
                    logger.warning(f"Erro ao buscar dados de rastreamento para oportunidade {opp_data.get('id')}: {str(tracking_error)}")
                    processed_opp.update({
                        'stage_tracking_calculo_pendente_date': None,
                        'stage_tracking_em_processamento_date': None,
                        'stage_tracking_calculo_concluido_date': None,
                        'stage_tracking_calculo_pendente_user': None
                    })
                
                processed_opportunities.append(OpportunityPowerBIData(**processed_opp))
                
            except Exception as e:
                logger.error(f"Erro ao processar oportunidade ID {opp_data.get('id', 'N/A')} da empresa {company_id}: {str(e)}")
                continue
        
        logger.info(f"Processadas {len(processed_opportunities)} oportunidades da empresa {company_id} para PowerBI")
        return processed_opportunities
        
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades da empresa {company_id} para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados das oportunidades da empresa: {str(e)}"
        )


async def fetch_opportunity_by_id_for_powerbi(opportunity_id: int) -> OpportunityPowerBIData:
    """
    Busca uma oportunidade específica do CRM por ID para PowerBI.
    
    Args:
        opportunity_id: ID da oportunidade para buscar.
    
    Returns:
        OpportunityPowerBIData da oportunidade especificada.
    
    Raises:
        HTTPException: Se a oportunidade não for encontrada ou houver erro.
    """
    try:
        odoo_client = await get_odoo_client()
        
        fields_to_fetch = [
            'id', 'create_date', 'name', 'x_studio_tese', 'partner_id',
            'user_id', 'team_id', 'activity_ids', 'expected_revenue', 'probability',
            'stage_id', 'active', 'won_status', 'lost_reason_id', 'state_id',
            'phone', 'email_from', 'street', 'city', 'zip', 'country_id',
            'x_studio_previsao_inss', 'x_studio_previsao_ipi', 
            'x_studio_previsao_irpj_e_csll', 'x_studio_previsao_pis_e_cofins',
            'x_studio_debitos', 'x_studio_ultima_atualizacao_de_estagio',
            'x_studio_ticket_de_1_anlise', 'x_studio_ticket_de_2_analise',
            'x_studio_probabilidade', 'x_studio_receita_bruta_esperada',
            'x_studio_faturamento_esperado', 'x_studio_honorrios_1',
            'write_date', 'date_closed', 'x_studio_tipo_de_oportunidade_1',
            'x_studio_data_calculo_pendente', 'x_studio_data_em_processamento_1',
            'x_studio_data_calculo_concluido', 'x_studio_usuario_calculo_concluido'
        ]
        
        # Search for specific opportunity by ID
        domain = [['id', '=', opportunity_id]]
        
        opportunities_data = await odoo_client.search_read(
            'crm.lead',
            domain=domain,
            fields=fields_to_fetch
        )
        
        if not opportunities_data:
            logger.warning(f"Oportunidade ID {opportunity_id} não encontrada")
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Oportunidade com ID {opportunity_id} não encontrada"
            )
        
        opp_data = opportunities_data[0]
        
        try:
            # Get field descriptions for selection fields
            x_studio_tese_desc = await _get_selection_field_description(
                odoo_client, 'crm.lead', 'x_studio_tese', opp_data.get('x_studio_tese')
            )
            
            processed_opp = {
                'id': opp_data.get('id'),
                'create_date': opp_data.get('create_date'),
                'name': opp_data.get('name'),
                'x_studio_tese': x_studio_tese_desc,
                'partner_id': _extract_relational_name(opp_data.get('partner_id')),
                'user_id': _extract_relational_name(opp_data.get('user_id')),
                'team_id': _extract_relational_name(opp_data.get('team_id')),
                'activity_ids': _format_activity_ids(opp_data.get('activity_ids')),
                'expected_revenue': opp_data.get('expected_revenue'),
                'probability': opp_data.get('probability'),
                'stage_id': _extract_relational_name(opp_data.get('stage_id')),
                'state_id': _extract_relational_name(opp_data.get('state_id')),
                'active': opp_data.get('active'),
                'won_status': opp_data.get('won_status'),
                'lost_reason_id': _extract_relational_name(opp_data.get('lost_reason_id')),
                'phone': opp_data.get('phone'),
                'email_from': opp_data.get('email_from'),
                'street': opp_data.get('street'),
                'city': opp_data.get('city'),
                'zip': opp_data.get('zip'),
                'country_id': _extract_relational_name(opp_data.get('country_id')),
                'x_studio_previsao_inss': opp_data.get('x_studio_previsao_inss'),
                'x_studio_previsao_ipi': opp_data.get('x_studio_previsao_ipi'),
                'x_studio_previsao_irpj_e_csll': opp_data.get('x_studio_previsao_irpj_e_csll'),
                'x_studio_previsao_pis_e_cofins': opp_data.get('x_studio_previsao_pis_e_cofins'),
                'x_studio_debitos': opp_data.get('x_studio_debitos'),
                'x_studio_ultima_atualizacao_de_estagio': opp_data.get('x_studio_ultima_atualizacao_de_estagio'),
                'x_studio_ticket_de_1_anlise': opp_data.get('x_studio_ticket_de_1_anlise'),
                'x_studio_ticket_de_2_analise': opp_data.get('x_studio_ticket_de_2_analise'),
                'x_studio_probabilidade': opp_data.get('x_studio_probabilidade'),
                'x_studio_receita_bruta_esperada': opp_data.get('x_studio_receita_bruta_esperada'),
                'x_studio_faturamento_esperado': opp_data.get('x_studio_faturamento_esperado'),
                'x_studio_honorrios_1': opp_data.get('x_studio_honorrios_1'),
                'write_date': opp_data.get('write_date'),
                'date_closed': opp_data.get('date_closed'),
                'x_studio_tipo_de_oportunidade_1': opp_data.get('x_studio_tipo_de_oportunidade_1'),
                'x_studio_data_calculo_pendente': opp_data.get('x_studio_data_calculo_pendente'),
                'x_studio_data_em_processamento_1': opp_data.get('x_studio_data_em_processamento_1'),
                'x_studio_data_calculo_concluido': opp_data.get('x_studio_data_calculo_concluido'),
                'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido'))
            }
            
            # Get additional partner data if needed
            partner_id = _extract_relational_id(opp_data.get('partner_id'))
            if partner_id:
                try:
                    partner_data = await odoo_client.search_read(
                        'res.partner',
                        domain=[['id', '=', partner_id]],
                        fields=['x_studio_categoria_economica']
                    )
                    
                    if partner_data:
                        partner_info = partner_data[0]
                        # Get categoria economica description
                        categoria_desc = await _get_selection_field_description(
                            odoo_client, 'res.partner', 'x_studio_categoria_economica', 
                            partner_info.get('x_studio_categoria_economica')
                        )
                        processed_opp['x_studio_categoria_economica'] = categoria_desc
                except Exception as partner_error:
                    logger.warning(f"Erro ao buscar dados do parceiro {partner_id}: {str(partner_error)}")
                    processed_opp['x_studio_categoria_economica'] = None
            else:
                processed_opp['x_studio_categoria_economica'] = None
            
            # Get stage tracking data from mail.message
            try:
                tracking_data = await get_opportunity_stage_tracking_data(opportunity_id)
                processed_opp.update({
                    'stage_tracking_calculo_pendente_date': tracking_data.get('calculo_pendente_date'),
                    'stage_tracking_em_processamento_date': tracking_data.get('em_processamento_date'),
                    'stage_tracking_calculo_concluido_date': tracking_data.get('calculo_concluido_date'),
                    'stage_tracking_calculo_pendente_user': tracking_data.get('calculo_pendente_user')
                })
            except Exception as tracking_error:
                logger.warning(f"Erro ao buscar dados de rastreamento para oportunidade {opportunity_id}: {str(tracking_error)}")
                processed_opp.update({
                    'stage_tracking_calculo_pendente_date': None,
                    'stage_tracking_em_processamento_date': None,
                    'stage_tracking_calculo_concluido_date': None,
                    'stage_tracking_calculo_pendente_user': None
                })
            
            opportunity = OpportunityPowerBIData(**processed_opp)
            logger.info(f"Oportunidade ID {opportunity_id} encontrada e processada para PowerBI")
            return opportunity
            
        except Exception as e:
            logger.error(f"Erro ao processar oportunidade ID {opportunity_id}: {str(e)}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Erro ao processar dados da oportunidade {opportunity_id}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidade ID {opportunity_id} para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados da oportunidade: {str(e)}"
        )


async def fetch_opportunities_for_powerbi() -> List[OpportunityPowerBIData]:
    """
    Busca todas as oportunidades do CRM com todos os campos necessários para PowerBI.
    
    Returns:
        Lista de OpportunityPowerBIData com todos os dados das oportunidades.
    """
    try:
        odoo_client = await get_odoo_client()
        
        fields_to_fetch = [
            'id', 'create_date', 'name', 'x_studio_tese', 'partner_id',
            'user_id', 'team_id', 'activity_ids', 'expected_revenue', 'probability',
            'stage_id', 'active', 'won_status', 'lost_reason_id', 'state_id',
            'phone', 'email_from', 'street', 'city', 'zip', 'country_id',
            'x_studio_previsao_inss', 'x_studio_previsao_ipi', 
            'x_studio_previsao_irpj_e_csll', 'x_studio_previsao_pis_e_cofins',
            'x_studio_debitos', 'x_studio_ultima_atualizacao_de_estagio',
            'x_studio_ticket_de_1_anlise', 'x_studio_ticket_de_2_analise',
            'x_studio_probabilidade', 'x_studio_receita_bruta_esperada',
            'x_studio_faturamento_esperado', 'x_studio_honorrios_1',
            'write_date', 'date_closed', 'x_studio_tipo_de_oportunidade_1',
            'x_studio_data_calculo_pendente', 'x_studio_data_em_processamento_1',
            'x_studio_data_calculo_concluido', 'x_studio_usuario_calculo_concluido'
        ]
        
        opportunities_data = await odoo_client.search_read(
            'crm.lead',
            domain=[],
            fields=fields_to_fetch
        )
        
        if not opportunities_data:
            logger.info("Nenhuma oportunidade encontrada no CRM")
            return []
        
        processed_opportunities = []
        
        for opp_data in opportunities_data:
            try:
                # Get field descriptions for selection fields
                x_studio_tese_desc = await _get_selection_field_description(
                    odoo_client, 'crm.lead', 'x_studio_tese', opp_data.get('x_studio_tese')
                )
                
                processed_opp = {
                    'id': opp_data.get('id'),
                    'create_date': opp_data.get('create_date'),
                    'name': opp_data.get('name'),
                    'x_studio_tese': x_studio_tese_desc,
                    'partner_id': _extract_relational_name(opp_data.get('partner_id')),
                    'user_id': _extract_relational_name(opp_data.get('user_id')),
                    'team_id': _extract_relational_name(opp_data.get('team_id')),
                    'activity_ids': _format_activity_ids(opp_data.get('activity_ids')),
                    'expected_revenue': opp_data.get('expected_revenue'),
                    'probability': opp_data.get('probability'),
                    'stage_id': _extract_relational_name(opp_data.get('stage_id')),
                    'state_id': _extract_relational_name(opp_data.get('state_id')),
                    'active': opp_data.get('active'),
                    'won_status': opp_data.get('won_status'),
                    'lost_reason_id': _extract_relational_name(opp_data.get('lost_reason_id')),
                    'phone': opp_data.get('phone'),
                    'email_from': opp_data.get('email_from'),
                    'street': opp_data.get('street'),
                    'city': opp_data.get('city'),
                    'zip': opp_data.get('zip'),
                    'country_id': _extract_relational_name(opp_data.get('country_id')),
                    'x_studio_previsao_inss': opp_data.get('x_studio_previsao_inss'),
                    'x_studio_previsao_ipi': opp_data.get('x_studio_previsao_ipi'),
                    'x_studio_previsao_irpj_e_csll': opp_data.get('x_studio_previsao_irpj_e_csll'),
                    'x_studio_previsao_pis_e_cofins': opp_data.get('x_studio_previsao_pis_e_cofins'),
                    'x_studio_debitos': opp_data.get('x_studio_debitos'),
                    'x_studio_ultima_atualizacao_de_estagio': opp_data.get('x_studio_ultima_atualizacao_de_estagio'),
                    'x_studio_ticket_de_1_anlise': opp_data.get('x_studio_ticket_de_1_anlise'),
                    'x_studio_ticket_de_2_analise': opp_data.get('x_studio_ticket_de_2_analise'),
                    'x_studio_probabilidade': opp_data.get('x_studio_probabilidade'),
                    'x_studio_receita_bruta_esperada': opp_data.get('x_studio_receita_bruta_esperada'),
                    'x_studio_faturamento_esperado': opp_data.get('x_studio_faturamento_esperado'),
                    'x_studio_honorrios_1': opp_data.get('x_studio_honorrios_1'),
                    'write_date': opp_data.get('write_date'),
                    'date_closed': opp_data.get('date_closed'),
                    'x_studio_tipo_de_oportunidade_1': opp_data.get('x_studio_tipo_de_oportunidade_1'),
                    'x_studio_data_calculo_pendente': opp_data.get('x_studio_data_calculo_pendente'),
                    'x_studio_data_em_processamento_1': opp_data.get('x_studio_data_em_processamento_1'),
                    'x_studio_data_calculo_concluido': opp_data.get('x_studio_data_calculo_concluido'),
                    'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido'))
                }
                
                # Get additional partner data if partner_id exists
                partner_id = _extract_relational_id(opp_data.get('partner_id'))
                if partner_id:
                    try:
                        partner_data = await odoo_client.search_read(
                            'res.partner',
                            domain=[['id', '=', partner_id]],
                            fields=['x_studio_categoria_economica']
                        )
                        
                        if partner_data:
                            partner_info = partner_data[0]
                            # Get categoria economica description
                            categoria_desc = await _get_selection_field_description(
                                odoo_client, 'res.partner', 'x_studio_categoria_economica', 
                                partner_info.get('x_studio_categoria_economica')
                            )
                            processed_opp['x_studio_categoria_economica'] = categoria_desc
                    except Exception as partner_error:
                        logger.warning(f"Erro ao buscar dados do parceiro {partner_id}: {str(partner_error)}")
                        processed_opp['x_studio_categoria_economica'] = None
                else:
                    processed_opp['x_studio_categoria_economica'] = None
                
                # Get stage tracking data from mail.message
                try:
                    tracking_data = await get_opportunity_stage_tracking_data(opp_data.get('id'))
                    processed_opp.update({
                        'stage_tracking_calculo_pendente_date': tracking_data.get('calculo_pendente_date'),
                        'stage_tracking_em_processamento_date': tracking_data.get('em_processamento_date'),
                        'stage_tracking_calculo_concluido_date': tracking_data.get('calculo_concluido_date'),
                        'stage_tracking_calculo_pendente_user': tracking_data.get('calculo_pendente_user')
                    })
                except Exception as tracking_error:
                    logger.warning(f"Erro ao buscar dados de rastreamento para oportunidade {opp_data.get('id')}: {str(tracking_error)}")
                    processed_opp.update({
                        'stage_tracking_calculo_pendente_date': None,
                        'stage_tracking_em_processamento_date': None,
                        'stage_tracking_calculo_concluido_date': None,
                        'stage_tracking_calculo_pendente_user': None
                    })
                
                processed_opportunities.append(OpportunityPowerBIData(**processed_opp))
                
            except Exception as e:
                logger.error(f"Erro ao processar oportunidade ID {opp_data.get('id', 'N/A')}: {str(e)}")
                continue
        
        logger.info(f"Processadas {len(processed_opportunities)} oportunidades para PowerBI")
        return processed_opportunities
        
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados das oportunidades: {str(e)}"
        )


def _extract_relational_name(field_value):
    """Extrai o nome de um campo relacional [ID, 'Nome'] ou retorna None."""
    if field_value is False:
        return None
    if isinstance(field_value, list) and len(field_value) >= 2:
        return field_value[1]
    return None


def _extract_relational_id(field_value):
    """Extrai o ID de um campo relacional [ID, 'Nome'] ou retorna None."""
    if field_value is False:
        return None
    if isinstance(field_value, list) and len(field_value) >= 1:
        return field_value[0]
    return None


def _format_activity_ids(activity_ids):
    """Formata lista de IDs de atividades para string."""
    if isinstance(activity_ids, list) and activity_ids:
        return ', '.join(map(str, activity_ids))
    return None


async def _get_selection_field_description(odoo_client, model_name: str, field_name: str, field_value):
    """Busca a descrição de um campo de seleção no Odoo."""
    if not field_value:
        return None
    
    try:
        # Busca as opções de seleção do campo
        fields_info = await odoo_client.execute_kw(
            model_name,
            'fields_get',
            [],
            {'attributes': ['selection']}
        )
        
        field_info = fields_info.get(field_name, {})
        selection_options = field_info.get('selection', [])
        
        # Busca a descrição correspondente ao valor
        for option_value, option_label in selection_options:
            if str(option_value) == str(field_value):
                return option_label
        
        # Se não encontrar, retorna o valor original
        return field_value
        
    except Exception as e:
        logger.warning(f"Erro ao buscar descrição do campo {field_name}: {str(e)}")
        return field_value


async def get_opportunity_stage_tracking_data(opportunity_id: int) -> Dict[str, Any]:
    """
    Busca dados de rastreamento de estágios de uma oportunidade do mail.message.
    
    Args:
        opportunity_id: ID da oportunidade para buscar dados de rastreamento
        
    Returns:
        Dicionário com as datas dos estágios e informações do usuário:
        {
            'calculo_pendente_date': datetime ou None,
            'em_processamento_date': datetime ou None, 
            'calculo_concluido_date': datetime ou None,
            'calculo_pendente_user': str ou None
        }
    """
    try:
        odoo_client = await get_odoo_client()
        
        # Buscar mensagens da oportunidade relacionadas a mudanças de estágio
        # Primeiro, buscar todas as mensagens para debug
        all_messages = await odoo_client.search_read(
            'mail.message',
            domain=[
                ['model', '=', 'crm.lead'],
                ['res_id', '=', opportunity_id]
            ],
            fields=['id', 'date', 'body', 'author_id', 'subtype_id', 'message_type', 'tracking_value_ids'],
            order='date asc'
        )
        
        # Buscar o subtype "Estágio alterado" 
        stage_subtype = await odoo_client.search_read(
            'mail.message.subtype',
            domain=[['name', '=', 'Estágio alterado']],
            fields=['id'],
            limit=1
        )
        
        stage_subtype_id = stage_subtype[0]['id'] if stage_subtype else None
        
        # Buscar mensagens específicas de mudança de estágio
        stage_change_messages = []
        if stage_subtype_id:
            stage_change_messages = await odoo_client.search_read(
                'mail.message',
                domain=[
                    ['model', '=', 'crm.lead'],
                    ['res_id', '=', opportunity_id],
                    ['subtype_id', '=', stage_subtype_id]
                ],
                fields=['id', 'date', 'author_id', 'tracking_value_ids'],
                order='date asc'
            )
        
        logger.debug(f"Encontradas {len(stage_change_messages)} mensagens de 'Estágio alterado' para oportunidade {opportunity_id}")
        
        # Buscar tracking values específicos das mensagens de mudança de estágio
        all_tracking_ids = []
        for msg in stage_change_messages:
            tracking_ids = msg.get('tracking_value_ids', [])
            all_tracking_ids.extend(tracking_ids)
        
        # Buscar o field_id para stage_id do modelo crm.lead
        stage_field = await odoo_client.search_read(
            'ir.model.fields',
            domain=[
                ['model', '=', 'crm.lead'],
                ['name', '=', 'stage_id']
            ],
            fields=['id'],
            limit=1
        )
        
        stage_field_id = stage_field[0]['id'] if stage_field else None
        logger.debug(f"Stage field ID encontrado: {stage_field_id}")
        
        relevant_tracking = []
        if all_tracking_ids:
            # Buscar todos os tracking values primeiro
            all_tracking_values = await odoo_client.search_read(
                'mail.tracking.value',
                domain=[['id', 'in', all_tracking_ids]],
                fields=['id', 'field_id', 'old_value_char', 'new_value_char', 'old_value_integer', 'new_value_integer', 'mail_message_id']
            )
            
            # Filtrar apenas os relacionados a stage_id
            for tv in all_tracking_values:
                field_id = tv.get('field_id')
                if field_id and isinstance(field_id, list):
                    field_id_value = field_id[0]
                    field_name = field_id[1] if len(field_id) > 1 else ""
                    
                    # Verificar se é o campo stage_id
                    if (stage_field_id and field_id_value == stage_field_id) or 'stage' in field_name.lower():
                        relevant_tracking.append(tv)
        
        logger.debug(f"Encontradas {len(all_messages)} mensagens e {len(relevant_tracking)} tracking values para oportunidade {opportunity_id}")
        
        messages = all_messages
        
        # Inicializar resultado
        tracking_data = {
            'calculo_pendente_date': None,
            'em_processamento_date': None,
            'calculo_concluido_date': None,
            'calculo_pendente_user': None
        }
        
        # Buscar nomes dos estágios no sistema para mapear IDs para nomes
        stage_names = await _get_stage_names(odoo_client)
        
        # Processar tracking values das mensagens de mudança de estágio
        for tracking in relevant_tracking:
            message_id = tracking.get('mail_message_id')
            if message_id:
                # Encontrar a mensagem correspondente nas mensagens de estágio
                stage_message = next((msg for msg in stage_change_messages if msg['id'] == message_id[0]), None)
                if stage_message:
                    message_date = stage_message.get('date')
                    author_id = stage_message.get('author_id')
                    
                    # Verificar se temos valores integer (IDs) ou char (nomes)
                    old_value_int = tracking.get('old_value_integer')
                    new_value_int = tracking.get('new_value_integer')
                    old_value_char = tracking.get('old_value_char', '')
                    new_value_char = tracking.get('new_value_char', '')
                    
                    # Usar o valor mais apropriado (priorizar char se disponível, senão int)
                    old_value = old_value_char if old_value_char else (stage_names.get(old_value_int, f"Stage ID: {old_value_int}") if old_value_int else "")
                    new_value = new_value_char if new_value_char else (stage_names.get(new_value_int, f"Stage ID: {new_value_int}") if new_value_int else "")
                    
                    logger.debug(f"Stage tracking encontrado: {old_value} → {new_value} em {message_date}")
                    
                    # Verificar mudanças para estágios específicos
                    if _stage_matches_target(new_value, 'Cálculo pendente', stage_names):
                        if not tracking_data['calculo_pendente_date']:
                            tracking_data['calculo_pendente_date'] = message_date
                            tracking_data['calculo_pendente_user'] = _extract_relational_name(author_id)
                            logger.info(f"✓ Encontrado mudança para 'Cálculo pendente' em {message_date}")
                            
                    elif _stage_matches_target(new_value, 'Em processamento', stage_names):
                        if not tracking_data['em_processamento_date']:
                            tracking_data['em_processamento_date'] = message_date
                            logger.info(f"✓ Encontrado mudança para 'Em processamento' em {message_date}")
                            
                    elif _stage_matches_target(new_value, 'Cálculo concluído', stage_names):
                        if not tracking_data['calculo_concluido_date']:
                            tracking_data['calculo_concluido_date'] = message_date
                            logger.info(f"✓ Encontrado mudança para 'Cálculo concluído' em {message_date}")
        
        # Se não encontrou tracking nas mensagens de "Estágio alterado", usar estratégia alternativa
        if not any(tracking_data.values()):
            logger.debug("Nenhum tracking encontrado em mensagens de 'Estágio alterado', usando método alternativo")
            
            # Buscar todas as mensagens com tracking values para esta oportunidade
            all_messages_with_tracking = await odoo_client.search_read(
                'mail.message',
                domain=[
                    ['model', '=', 'crm.lead'],
                    ['res_id', '=', opportunity_id],
                    ['tracking_value_ids', '!=', False]
                ],
                fields=['id', 'date', 'author_id', 'tracking_value_ids'],
                order='date asc'
            )
            
            logger.debug(f"Encontradas {len(all_messages_with_tracking)} mensagens com tracking values (método alternativo)")
            
            # Processar essas mensagens com a mesma lógica
            for msg in all_messages_with_tracking:
                tracking_ids = msg.get('tracking_value_ids', [])
                if tracking_ids:
                    # Buscar tracking values desta mensagem
                    msg_tracking_values = await odoo_client.search_read(
                        'mail.tracking.value',
                        domain=[['id', 'in', tracking_ids]],
                        fields=['id', 'field_id', 'old_value_char', 'new_value_char', 'old_value_integer', 'new_value_integer']
                    )
                    
                    for tv in msg_tracking_values:
                        field_id = tv.get('field_id')
                        if field_id and isinstance(field_id, list):
                            field_id_value = field_id[0]
                            field_name = field_id[1] if len(field_id) > 1 else ""
                            
                            # Verificar se é o campo stage_id
                            if (stage_field_id and field_id_value == stage_field_id) or 'stage' in field_name.lower():
                                message_date = msg.get('date')
                                author_id = msg.get('author_id')
                                
                                # Processar valores
                                old_value_char = tv.get('old_value_char', '')
                                new_value_char = tv.get('new_value_char', '')
                                new_value_int = tv.get('new_value_integer')
                                
                                new_value = new_value_char if new_value_char else (stage_names.get(new_value_int, f"Stage ID: {new_value_int}") if new_value_int else "")
                                
                                logger.debug(f"Alternative stage tracking: → {new_value} em {message_date}")
                                
                                # Verificar mudanças para estágios específicos
                                if _stage_matches_target(new_value, 'Cálculo pendente', stage_names):
                                    if not tracking_data['calculo_pendente_date']:
                                        tracking_data['calculo_pendente_date'] = message_date
                                        tracking_data['calculo_pendente_user'] = _extract_relational_name(author_id)
                                        logger.info(f"✓ Alternative: Encontrado 'Cálculo pendente' em {message_date}")
                                        
                                elif _stage_matches_target(new_value, 'Em processamento', stage_names):
                                    if not tracking_data['em_processamento_date']:
                                        tracking_data['em_processamento_date'] = message_date
                                        logger.info(f"✓ Alternative: Encontrado 'Em processamento' em {message_date}")
                                        
                                elif _stage_matches_target(new_value, 'Cálculo concluído', stage_names):
                                    if not tracking_data['calculo_concluido_date']:
                                        tracking_data['calculo_concluido_date'] = message_date
                                        logger.info(f"✓ Alternative: Encontrado 'Cálculo concluído' em {message_date}")
        
        # Fallback final: Analisar corpo das mensagens para encontrar mudanças de estágio
        if not any(tracking_data.values()):
            logger.debug(f"Fallback: analisando {len(messages)} mensagens por conteúdo")
            for message in messages:
                body = message.get('body', '')
                message_date = message.get('date')
                author_id = message.get('author_id')
                message_type = message.get('message_type', '')
                
                # Log de todas as mensagens para debug
                logger.debug(f"Analisando mensagem {message.get('id')}: tipo={message_type}, data={message_date}, body={body[:100]}...")
                
                # Verificar se a mensagem é sobre mudança de estágio
                if ('Estágio' in body or 'Stage' in body or 'estágio' in body.lower()) and message_date:
                    logger.debug(f"Mensagem de estágio encontrada para oportunidade {opportunity_id}: {body[:100]}...")
                    
                    # Buscar estágios específicos no corpo da mensagem  
                    if _contains_stage_reference(body, 'Cálculo pendente', stage_names):
                        if not tracking_data['calculo_pendente_date']:
                            tracking_data['calculo_pendente_date'] = message_date
                            tracking_data['calculo_pendente_user'] = _extract_relational_name(author_id)
                            logger.debug(f"Encontrado estágio 'Cálculo pendente' em {message_date}")
                            
                    elif _contains_stage_reference(body, 'Em processamento', stage_names):
                        if not tracking_data['em_processamento_date']:
                            tracking_data['em_processamento_date'] = message_date
                            logger.debug(f"Encontrado estágio 'Em processamento' em {message_date}")
                            
                    elif _contains_stage_reference(body, 'Cálculo concluído', stage_names):
                        if not tracking_data['calculo_concluido_date']:
                            tracking_data['calculo_concluido_date'] = message_date
                            logger.debug(f"Encontrado estágio 'Cálculo concluído' em {message_date}")
        
        # Estratégia final: Se nenhum tracking foi encontrado, tentar usar dados existentes na oportunidade
        if not any(tracking_data.values()):
            logger.debug("Nenhum tracking encontrado em mensagens, tentando usar dados da oportunidade")
            
            # Buscar dados da oportunidade atual
            opportunity_data = await odoo_client.search_read(
                'crm.lead',
                domain=[['id', '=', opportunity_id]],
                fields=[
                    'stage_id', 'write_date', 'user_id',
                    'x_studio_data_calculo_pendente',
                    'x_studio_data_em_processamento_1', 
                    'x_studio_data_calculo_concluido',
                    'x_studio_usuario_calculo_concluido'
                ]
            )
            
            if opportunity_data:
                opp = opportunity_data[0]
                current_stage = _extract_relational_name(opp.get('stage_id'))
                current_user = _extract_relational_name(opp.get('user_id'))
                
                logger.debug(f"Estágio atual: {current_stage}")
                
                # Se já temos os campos customizados, usar eles
                if opp.get('x_studio_data_calculo_pendente'):
                    tracking_data['calculo_pendente_date'] = opp.get('x_studio_data_calculo_pendente')
                    tracking_data['calculo_pendente_user'] = current_user
                    
                if opp.get('x_studio_data_em_processamento_1'):
                    tracking_data['em_processamento_date'] = opp.get('x_studio_data_em_processamento_1')
                    
                if opp.get('x_studio_data_calculo_concluido'):
                    tracking_data['calculo_concluido_date'] = opp.get('x_studio_data_calculo_concluido')
                
                # Se o estágio atual for um dos que estamos rastreando e não temos data, usar write_date
                elif current_stage:
                    write_date = opp.get('write_date')
                    if _stage_matches_target(current_stage, 'Cálculo pendente', stage_names):
                        tracking_data['calculo_pendente_date'] = write_date
                        tracking_data['calculo_pendente_user'] = current_user
                    elif _stage_matches_target(current_stage, 'Em processamento', stage_names):
                        tracking_data['em_processamento_date'] = write_date
                    elif _stage_matches_target(current_stage, 'Cálculo concluído', stage_names):
                        tracking_data['calculo_concluido_date'] = write_date

        logger.info(f"Dados de rastreamento extraídos para oportunidade {opportunity_id}")
        return tracking_data
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de rastreamento da oportunidade {opportunity_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados de rastreamento: {str(e)}"
        )


async def _get_stage_names(odoo_client) -> Dict[int, str]:
    """Busca nomes dos estágios do CRM para facilitar identificação."""
    try:
        stages = await odoo_client.search_read(
            'crm.stage',
            domain=[],
            fields=['id', 'name']
        )
        return {stage['id']: stage['name'] for stage in stages}
    except Exception as e:
        logger.warning(f"Erro ao buscar nomes dos estágios: {str(e)}")
        return {}


def _contains_stage_reference(body: str, stage_name: str, stage_names: Dict[int, str]) -> bool:
    """
    Verifica se o corpo da mensagem contém referência ao estágio específico.
    
    Args:
        body: Corpo da mensagem HTML
        stage_name: Nome do estágio procurado
        stage_names: Dicionário com nomes dos estágios
        
    Returns:
        True se encontrar referência ao estágio
    """
    # Remover tags HTML para facilitar busca
    import re
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    clean_body = clean_body.lower().strip()
    
    # Variações do nome do estágio para buscar
    stage_variations = [
        stage_name.lower(),
        stage_name.lower().replace(' ', ''),
        stage_name.lower().replace('á', 'a').replace('ç', 'c').replace('ã', 'a')
    ]
    
    # Buscar pelo nome do estágio diretamente
    for variation in stage_variations:
        if variation in clean_body:
            return True
    
    # Buscar pelos nomes dos estágios do sistema
    for stage_id, name in stage_names.items():
        if name:
            name_lower = name.lower()
            # Verifica se o nome do estágio do sistema contém o estágio procurado
            for variation in stage_variations:
                if variation in name_lower and name_lower in clean_body:
                    return True
    
    # Busca específica para padrões comuns do Odoo
    # Ex: "Em processamento → Cálculo concluído"
    stage_patterns = {
        'cálculo pendente': ['calculo pendente', 'calculopendente', 'calculo_pendente'],
        'em processamento': ['em processamento', 'emprocessamento', 'em_processamento'],
        'cálculo concluído': ['calculo concluido', 'calculoconcluido', 'calculo_concluido', 'cálculo concluído']
    }
    
    target_patterns = stage_patterns.get(stage_name.lower(), [])
    for pattern in target_patterns:
        if pattern in clean_body:
            return True
    
    return False


def _stage_matches_target(stage_value: str, target_stage: str, stage_names: Dict[int, str]) -> bool:
    """
    Verifica se um valor de estágio corresponde ao estágio alvo.
    
    Args:
        stage_value: Valor do estágio (pode ser nome ou ID)
        target_stage: Nome do estágio que estamos procurando
        stage_names: Dicionário com mapeamento de IDs para nomes
        
    Returns:
        True se o estágio corresponder ao alvo
    """
    if not stage_value:
        return False
    
    # Normalizar strings para comparação
    target_lower = target_stage.lower().strip()
    stage_lower = str(stage_value).lower().strip()
    
    # Busca direta no nome
    if target_lower in stage_lower:
        return True
    
    # Buscar por padrões específicos
    stage_patterns = {
        'cálculo pendente': ['calculo pendente', 'calculopendente', 'calculo_pendente', 'pendente'],
        'em processamento': ['em processamento', 'emprocessamento', 'em_processamento', 'processamento'],
        'cálculo concluído': ['calculo concluido', 'calculoconcluido', 'calculo_concluido', 'concluido', 'concluído']
    }
    
    target_patterns = stage_patterns.get(target_lower, [])
    for pattern in target_patterns:
        if pattern in stage_lower:
            return True
    
    # Verificar se é um ID numérico e corresponde a um estágio conhecido
    try:
        stage_id = int(stage_value)
        stage_name = stage_names.get(stage_id, '').lower()
        if stage_name:
            for pattern in target_patterns:
                if pattern in stage_name:
                    return True
            if target_lower in stage_name:
                return True
    except ValueError:
        pass
    
    return False

