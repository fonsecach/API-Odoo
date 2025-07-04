
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
            'user_id', 'team_id', 'activity_ids', 'expected_revenue',
            'stage_id', 'active', 'won_status', 'lost_reason_id', 'state_id',
            'phone', 'email_from', 'city', 'zip',
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
                'activity_ids': await _get_latest_activity_summary(odoo_client, opp_data.get('activity_ids')),
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
                'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido')),
                'x_studio_usuario_calculo_pendente': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_pendente')),
                'x_studio_usuario_em_processamento': _extract_relational_name(opp_data.get('x_studio_usuario_em_processamento'))
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
            
            # Usar campos existentes ao invés de rastreamento via mail.message (performance)
            processed_opp.update({
                'stage_tracking_calculo_pendente_date': opp_data.get('x_studio_data_calculo_pendente'),
                'stage_tracking_em_processamento_date': opp_data.get('x_studio_data_em_processamento_1'),
                'stage_tracking_calculo_concluido_date': opp_data.get('x_studio_data_calculo_concluido'),
                'stage_tracking_calculo_pendente_user': _extract_relational_name(opp_data.get('user_id'))
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
            'user_id', 'team_id', 'activity_ids', 'expected_revenue',
            'stage_id', 'active', 'won_status', 'lost_reason_id', 'state_id',
            'phone', 'email_from', 'city', 'zip',
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
                    'activity_ids': await _get_latest_activity_summary(odoo_client, opp_data.get('activity_ids')),
                    'expected_revenue': opp_data.get('expected_revenue'),
                    'stage_id': _extract_relational_name(opp_data.get('stage_id')),
                    'state_id': _extract_relational_name(opp_data.get('state_id')),
                    'active': opp_data.get('active'),
                    'won_status': opp_data.get('won_status'),
                    'lost_reason_id': _extract_relational_name(opp_data.get('lost_reason_id')),
                    'phone': opp_data.get('phone'),
                    'email_from': opp_data.get('email_from'),
                    'city': opp_data.get('city'),
                    'zip': opp_data.get('zip'),
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
                
                # Usar campos existentes ao invés de rastreamento via mail.message (performance)
                processed_opp.update({
                    'stage_tracking_prospect_date': None,
                    'stage_tracking_prospect_user': None,
                    'stage_tracking_primeira_reuniao_date': None,
                    'stage_tracking_primeira_reuniao_user': None,
                    'stage_tracking_aguardando_documentacao_date': None,
                    'stage_tracking_aguardando_documentacao_user': None,
                    'stage_tracking_calculo_pendente_date': opp_data.get('x_studio_data_calculo_pendente'),
                    'stage_tracking_calculo_pendente_user': _extract_relational_name(opp_data.get('user_id')),
                    'stage_tracking_em_processamento_date': opp_data.get('x_studio_data_em_processamento_1'),
                    'stage_tracking_em_processamento_user': _extract_relational_name(opp_data.get('user_id')),
                    'stage_tracking_calculo_concluido_date': opp_data.get('x_studio_data_calculo_concluido'),
                    'stage_tracking_calculo_concluido_user': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido')),
                    'stage_tracking_revisao_de_calculo_date': None,
                    'stage_tracking_revisao_de_calculo_user': None,
                    'stage_tracking_apresentacao_date': None,
                    'stage_tracking_apresentacao_user': None,
                    'stage_tracking_em_negociacao_date': None,
                    'stage_tracking_em_negociacao_user': None
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
    """Extrai o nome de um campo relacional [ID, 'Nome'] ou retorna o valor se for string."""
    if field_value is False:
        return None
    if isinstance(field_value, list) and len(field_value) >= 2:
        return field_value[1]
    if isinstance(field_value, str):
        return field_value
    return None


def _extract_relational_id(field_value):
    """Extrai o ID de um campo relacional [ID, 'Nome'] ou retorna None."""
    if field_value is False:
        return None
    if isinstance(field_value, list) and len(field_value) >= 1:
        return field_value[0]
    return None


async def _get_latest_activity_summary(odoo_client, activity_ids):
    """
    Busca apenas o nome da última atividade registrada (otimizado para performance).
    
    Args:
        odoo_client: Cliente Odoo assíncrono
        activity_ids: Lista de IDs de atividades
        
    Returns:
        String com nome da última atividade ou None
    """
    if not activity_ids or not isinstance(activity_ids, list) or len(activity_ids) == 0:
        return None
    
    try:
        # Buscar apenas o nome da atividade mais recente (ultra otimizado)
        activities = await odoo_client.search_read(
            'mail.activity',
            domain=[['id', 'in', activity_ids]],
            fields=['activity_type_id'],
            order='create_date desc',
            limit=1
        )
        
        if not activities:
            return None
        
        # Extrair apenas o nome do tipo de atividade
        activity_type = activities[0].get('activity_type_id')
        if activity_type and isinstance(activity_type, list) and len(activity_type) > 1:
            return activity_type[1]
        
        return None
        
    except Exception as e:
        logger.warning(f"Erro ao buscar última atividade: {str(e)}")
        return None


def _format_activity_ids(activity_ids):
    """Formata lista de IDs de atividades para string (função legada)."""
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
    Busca dados de rastreamento de estágios usando apenas campos customizados (otimizado).
    
    Args:
        opportunity_id: ID da oportunidade para buscar dados de rastreamento
        
    Returns:
        Dicionário com as datas dos estágios importantes:
        {
            'calculo_pendente_date': datetime ou None,
            'calculo_pendente_user': str ou None,
            'em_processamento_date': datetime ou None,
            'em_processamento_user': str ou None,
            'calculo_concluido_date': datetime ou None,
            'calculo_concluido_user': str ou None
        }
    """
    try:
        odoo_client = await get_odoo_client()
        
        # Buscar apenas dados da oportunidade com campos customizados
        opportunity_data = await odoo_client.search_read(
            'crm.lead',
            domain=[['id', '=', opportunity_id]],
            fields=[
                'user_id',
                'x_studio_data_calculo_pendente',
                'x_studio_data_em_processamento_1', 
                'x_studio_data_calculo_concluido',
                'x_studio_usuario_calculo_concluido'
            ]
        )
        
        if not opportunity_data:
            logger.warning(f"Oportunidade ID {opportunity_id} não encontrada")
            return {
                'calculo_pendente_date': None,
                'calculo_pendente_user': None,
                'em_processamento_date': None,
                'em_processamento_user': None,
                'calculo_concluido_date': None,
                'calculo_concluido_user': None
            }
        
        opp = opportunity_data[0]
        current_user = _extract_relational_name(opp.get('user_id'))
        
        # Usar campos customizados diretamente
        tracking_data = {
            'calculo_pendente_date': opp.get('x_studio_data_calculo_pendente'),
            'calculo_pendente_user': current_user,
            'em_processamento_date': opp.get('x_studio_data_em_processamento_1'),
            'em_processamento_user': current_user,
            'calculo_concluido_date': opp.get('x_studio_data_calculo_concluido'),
            'calculo_concluido_user': _extract_relational_name(opp.get('x_studio_usuario_calculo_concluido'))
        }

        logger.info(f"Dados de rastreamento extraídos para oportunidade {opportunity_id}")
        return tracking_data
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados de rastreamento da oportunidade {opportunity_id}: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados de rastreamento: {str(e)}"
        )



