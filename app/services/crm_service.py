
import logging
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

# Importa as configurações de conexão do Odoo
from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import OpportunityCreateIntelligent, OpportunityPowerBIData, OpportunityCreateUnified, OpportunityReturn

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


import re
import base64


def validate_cpf_cnpj(document: str) -> str:
    """
    Valida e limpa CPF ou CNPJ, retornando apenas os dígitos.
    
    Args:
        document: CPF ou CNPJ a ser validado
        
    Returns:
        Documento limpo com apenas dígitos
        
    Raises:
        ValueError: Se o documento for inválido
    """
    if not document:
        raise ValueError("CPF/CNPJ não pode estar vazio")
    
    # Remove todos os caracteres não numéricos
    document_clean = re.sub(r'[^0-9]', '', document)
    
    # Verifica se tem 11 dígitos (CPF) ou 14 dígitos (CNPJ)
    if len(document_clean) == 11:
        return document_clean  # CPF válido
    elif len(document_clean) == 14:
        return document_clean  # CNPJ válido
    else:
        raise ValueError("Documento deve conter 11 dígitos (CPF) ou 14 dígitos (CNPJ)")
    
    return document_clean


async def create_opportunity_unified(opportunity_data: OpportunityCreateUnified) -> OpportunityReturn:
    """
    Serviço unificado para criação de oportunidades.
    
    Funcionalidades:
    - Valida CPF/CNPJ se fornecido
    - Verifica/cria cliente automaticamente se dados fornecidos
    - Cria oportunidade com campos personalizados
    - Processa anexos em base64
    
    Args:
        opportunity_data: Dados da oportunidade
        
    Returns:
        Dados da oportunidade criada
        
    Raises:
        HTTPException: Em caso de erro na criação
    """
    try:
        # Obter cliente Odoo
        odoo_client = await get_odoo_client()
        
        partner_id = None
        
        # Se company_cnpj foi fornecido, valida e busca/cria parceiro
        if opportunity_data.company_cnpj:
            document_clean = validate_cpf_cnpj(opportunity_data.company_cnpj)
            
            # Buscar ou criar parceiro/cliente
            partner_id = await get_or_create_partner_by_vat(
                vat_number=document_clean,
                company_name=opportunity_data.company_name or "Cliente"
            )
            
            if not partner_id:
                logger.error(f"Falha ao obter/criar parceiro para documento {document_clean}")
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Não foi possível criar/encontrar cliente para documento {document_clean}"
                )
        
        # Preparar dados da oportunidade
        opp_data = {
            'name': opportunity_data.name,
            'user_id': opportunity_data.user_id,
            'type': 'opportunity',
            'active': True,
        }
        
        # Adicionar partner_id se foi criado/encontrado
        if partner_id:
            opp_data['partner_id'] = partner_id
        
        # Adicionar campos opcionais se fornecidos
        if opportunity_data.team_id:
            opp_data['team_id'] = opportunity_data.team_id
        
        if opportunity_data.expected_revenue is not None:
            opp_data['expected_revenue'] = opportunity_data.expected_revenue
        
        if opportunity_data.x_studio_tese:
            opp_data['x_studio_tese'] = opportunity_data.x_studio_tese
        
        if opportunity_data.x_studio_selection_field_37f_1ibrq64l3:
            opp_data['x_studio_selection_field_37f_1ibrq64l3'] = opportunity_data.x_studio_selection_field_37f_1ibrq64l3
        
        if opportunity_data.x_studio_identificador_marketing:
            opp_data['x_studio_identificador_marketing'] = opportunity_data.x_studio_identificador_marketing
        
        if opportunity_data.x_studio_origem_marketing:
            opp_data['x_studio_origem_marketing'] = opportunity_data.x_studio_origem_marketing
        
        # Criar oportunidade
        opportunity_id = await odoo_client.create('crm.lead', opp_data)
        
        if not opportunity_id:
            logger.error(f"Falha ao criar oportunidade para {opportunity_data.company_name}")
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail="Não foi possível criar a oportunidade"
            )
        
        # Processar anexos se fornecidos
        if opportunity_data.files:
            for i, file_base64 in enumerate(opportunity_data.files):
                try:
                    # Decodificar base64
                    file_data = base64.b64decode(file_base64)
                    
                    # Criar anexo
                    attachment_data = {
                        'name': f"attachment_{i+1}_{opportunity_id}.pdf",
                        'datas': file_base64,
                        'res_model': 'crm.lead',
                        'res_id': opportunity_id,
                        'type': 'binary'
                    }
                    
                    attachment_id = await odoo_client.create('ir.attachment', attachment_data)
                    logger.info(f"Anexo {attachment_id} criado para oportunidade {opportunity_id}")
                    
                except Exception as e:
                    logger.warning(f"Erro ao processar anexo {i+1} para oportunidade {opportunity_id}: {str(e)}")
                    # Continua o processamento mesmo com erro no anexo
        
        # Buscar dados da oportunidade criada para retorno
        opportunity_details = await odoo_client.search_read(
            'crm.lead',
            domain=[['id', '=', opportunity_id]],
            fields=['name', 'partner_id', 'user_id', 'team_id', 'stage_id', 'expected_revenue']
        )
        
        if not opportunity_details:
            logger.error(f"Não foi possível buscar detalhes da oportunidade {opportunity_id}")
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail="Oportunidade criada mas não foi possível buscar detalhes"
            )
        
        details = opportunity_details[0]
        
        # Função auxiliar para extrair ID de campos relacionais
        def extract_id(field_value):
            if isinstance(field_value, list) and field_value:
                return field_value[0]
            return field_value if field_value not in [False, None] else None
        
        # Preparar dados de retorno
        return_data = {
            'opportunity_id': opportunity_id,
            'name': details.get('name'),
            'partner_id': extract_id(details.get('partner_id')),
            'user_id': extract_id(details.get('user_id')),
            'team_id': extract_id(details.get('team_id')),
            'stage_id': extract_id(details.get('stage_id')),
            'expected_revenue': details.get('expected_revenue', 0.0),
        }
        
        logger.info(f"Oportunidade {opportunity_id} criada com sucesso: {opportunity_data.name}")
        return OpportunityReturn(**return_data)
        
    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Erro de validação: {str(ve)}")
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        logger.exception(f"Erro inesperado ao criar oportunidade: {opportunity_data.name}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar oportunidade: {str(e)}"
        )

