import logging
from http import HTTPStatus
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import OpportunityPowerBIData
from app.services.async_odoo_client import AsyncOdooClient

logger = logging.getLogger(__name__)


async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


async def _get_selection_field_mapping(odoo_client, model_name: str, field_name: str) -> Dict[str, str]:
    """
    Busca o mapeamento completo de um campo de seleção no Odoo.
    Retorna um dicionário com {valor: descrição} para uso em batch.
    """
    try:
        fields_info = await odoo_client.execute_kw(
            model_name,
            'fields_get',
            [],
            {'attributes': ['selection']}
        )
        
        field_info = fields_info.get(field_name, {})
        selection_options = field_info.get('selection', [])
        
        # Criar mapeamento valor -> descrição
        mapping = {}
        for option_value, option_label in selection_options:
            mapping[str(option_value)] = option_label
        
        return mapping
        
    except Exception as e:
        logger.warning(f"Erro ao buscar mapeamento do campo {field_name}: {str(e)}")
        return {}


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


async def fetch_opportunities_for_powerbi_optimized() -> List[OpportunityPowerBIData]:
    """
    Busca todas as oportunidades do CRM com todos os campos necessários para PowerBI.
    Versão otimizada para performance com bulk operations.
    
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
        
        # Otimização 1: Buscar dados de parceiros em batch
        partner_ids = [_extract_relational_id(opp.get('partner_id')) for opp in opportunities_data]
        partner_ids = [pid for pid in partner_ids if pid is not None]
        
        partner_data_map = {}
        if partner_ids:
            partner_data_bulk = await odoo_client.search_read(
                'res.partner',
                domain=[['id', 'in', partner_ids]],
                fields=['id', 'x_studio_categoria_economica']
            )
            partner_data_map = {p['id']: p for p in partner_data_bulk}
        
        # Otimização 2: Buscar atividades em batch
        activity_ids = []
        for opp in opportunities_data:
            if opp.get('activity_ids'):
                activity_ids.extend(opp.get('activity_ids'))
        
        activity_data_map = {}
        if activity_ids:
            activity_data_bulk = await odoo_client.search_read(
                'mail.activity',
                domain=[['id', 'in', activity_ids]],
                fields=['id', 'activity_type_id', 'create_date'],
                order='create_date desc'
            )
            # Agrupar por ID de atividade
            for activity in activity_data_bulk:
                if activity.get('activity_type_id'):
                    activity_data_map[activity['id']] = activity
        
        # Otimização 3: Buscar selection fields descriptions em batch
        tese_selection_map = await _get_selection_field_mapping(
            odoo_client, 'crm.lead', 'x_studio_tese'
        )
        
        categoria_selection_map = await _get_selection_field_mapping(
            odoo_client, 'res.partner', 'x_studio_categoria_economica'
        )
        
        processed_opportunities = []
        
        for opp_data in opportunities_data:
            try:
                # Usar mapeamento pré-carregado para tese
                tese_value = str(opp_data.get('x_studio_tese', ''))
                x_studio_tese_desc = tese_selection_map.get(tese_value, tese_value)
                
                # Buscar dados do parceiro do mapeamento
                partner_id = _extract_relational_id(opp_data.get('partner_id'))
                categoria_desc = None
                if partner_id and partner_id in partner_data_map:
                    partner_info = partner_data_map[partner_id]
                    categoria_value = str(partner_info.get('x_studio_categoria_economica', ''))
                    categoria_desc = categoria_selection_map.get(categoria_value, categoria_value)
                
                # Buscar última atividade do mapeamento
                activity_summary = None
                if opp_data.get('activity_ids'):
                    for activity_id in opp_data.get('activity_ids'):
                        if activity_id in activity_data_map:
                            activity_info = activity_data_map[activity_id]
                            activity_type = activity_info.get('activity_type_id')
                            if activity_type and isinstance(activity_type, list) and len(activity_type) > 1:
                                activity_summary = activity_type[1]
                                break
                
                processed_opp = {
                    'id': opp_data.get('id'),
                    'create_date': opp_data.get('create_date'),
                    'name': opp_data.get('name'),
                    'x_studio_tese': x_studio_tese_desc,
                    'partner_id': _extract_relational_name(opp_data.get('partner_id')),
                    'user_id': _extract_relational_name(opp_data.get('user_id')),
                    'team_id': _extract_relational_name(opp_data.get('team_id')),
                    'activity_ids': activity_summary,
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
                    'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido')),
                    'x_studio_categoria_economica': categoria_desc
                }
                
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
        
        logger.debug(f"Processadas {len(processed_opportunities)} oportunidades para PowerBI (otimizado)")
        return processed_opportunities
        
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados das oportunidades: {str(e)}"
        )


async def fetch_opportunities_for_powerbi_with_pt_names_optimized() -> List[dict]:
    """
    Busca todas as oportunidades do CRM com campos em português para PowerBI.
    Remove campos conforme solicitado: probability, street, country_id
    Versão otimizada para performance.
    
    Returns:
        Lista de dicionários com dados das oportunidades com nomes em português.
    """
    try:
        # Usa a função otimizada para buscar dados processados
        opportunities_data = await fetch_opportunities_for_powerbi_optimized()
        
        # Mapeia para o formato com nomes em português
        portuguese_opportunities = []
        for opp in opportunities_data:
            opp_dict = opp.dict() if hasattr(opp, 'dict') else opp
            mapped_opp = _map_to_powerbi_response(opp_dict)  
            portuguese_opportunities.append(mapped_opp)
        
        logger.debug(f"Processadas {len(portuguese_opportunities)} oportunidades com nomes em português para PowerBI (otimizado)")
        return portuguese_opportunities
        
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidades com nomes em português para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados das oportunidades: {str(e)}"
        )


def _map_to_powerbi_response(processed_opp: dict) -> dict:
    """
    Mapeia dados processados de oportunidade para o formato de resposta PowerBI com nomes em português.
    Remove campos conforme solicitado: probability, street, country_id
    """
    return {
        'id': processed_opp.get('id'),
        'CriadoEm': processed_opp.get('create_date'),
        'Oportunidade': processed_opp.get('name'),
        'Tese': processed_opp.get('x_studio_tese'),
        'Cliente': processed_opp.get('partner_id'),
        'Estado': processed_opp.get('state_id'),
        'Vendedor': processed_opp.get('user_id'),
        'EquipeDeVendas': processed_opp.get('team_id'),
        'UltimaAtividade': processed_opp.get('activity_ids'),
        'ReceitaEsperada': processed_opp.get('expected_revenue'),
        'Estagio': processed_opp.get('stage_id'),
        'Segmento': processed_opp.get('x_studio_categoria_economica'),
        'Ativo': processed_opp.get('active'),
        'StatusGanhoPerda': processed_opp.get('won_status'),
        'MotivoDaPerda': processed_opp.get('lost_reason_id'),
        'PrevisaoInss': processed_opp.get('x_studio_previsao_inss'),
        'PrevisaoIpi': processed_opp.get('x_studio_previsao_ipi'),
        'PrevisaoIrpjCsll': processed_opp.get('x_studio_previsao_irpj_e_csll'),
        'PrevisaoPisCofins': processed_opp.get('x_studio_previsao_pis_e_cofins'),
        'Debitos': processed_opp.get('x_studio_debitos'),
        'UltimaAtualizacaoDeEstagio': processed_opp.get('x_studio_ultima_atualizacao_de_estagio'),
        'TicketDePrimeiraAnalise': processed_opp.get('x_studio_ticket_de_1_anlise'),
        'TicketDeSegundaAnalise': processed_opp.get('x_studio_ticket_de_2_analise'),
        'Probabilidade': processed_opp.get('x_studio_probabilidade'),
        'ReceitaBrutaEsperada': processed_opp.get('x_studio_receita_bruta_esperada'),
        'FaturamentoEsperado': processed_opp.get('x_studio_faturamento_esperado'),
        'Honorarios': processed_opp.get('x_studio_honorrios_1'),
        'UltimaAtualizacao': processed_opp.get('write_date'),
        'DataDeGanhoOuPerda': processed_opp.get('date_closed'),
        'TipoDeOportunidade': processed_opp.get('x_studio_tipo_de_oportunidade_1'),
        'Telefone': processed_opp.get('phone'),
        'Email': processed_opp.get('email_from'),
        'Cidade': processed_opp.get('city'),
        'CEP': processed_opp.get('zip'),
        'DataCalculoPendente': processed_opp.get('x_studio_data_calculo_pendente'),
        'DataEmProcessamento': processed_opp.get('x_studio_data_em_processamento_1'),
        'DataCalculoConcluido': processed_opp.get('x_studio_data_calculo_concluido'),
        'UsuarioCalculoConcluido': processed_opp.get('x_studio_usuario_calculo_concluido'),
    }


async def fetch_opportunity_by_id_for_powerbi_with_pt_names_optimized(opportunity_id: int) -> dict:
    """
    Busca uma oportunidade específica por ID com campos em português para PowerBI.
    Versão otimizada para performance.
    
    Args:
        opportunity_id: ID da oportunidade a ser buscada
        
    Returns:
        Dicionário com dados da oportunidade com nomes em português.
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
        
        # Buscar dados relacionados em batch
        partner_id = _extract_relational_id(opp_data.get('partner_id'))
        
        # Buscar dados do parceiro se existir
        partner_data = None
        if partner_id:
            partner_data_bulk = await odoo_client.search_read(
                'res.partner',
                domain=[['id', '=', partner_id]],
                fields=['x_studio_categoria_economica']
            )
            partner_data = partner_data_bulk[0] if partner_data_bulk else None
        
        # Buscar atividades se existirem
        activity_summary = None
        if opp_data.get('activity_ids'):
            activity_data_bulk = await odoo_client.search_read(
                'mail.activity',
                domain=[['id', 'in', opp_data.get('activity_ids')]],
                fields=['activity_type_id', 'create_date'],
                order='create_date desc',
                limit=1
            )
            if activity_data_bulk:
                activity_info = activity_data_bulk[0]
                activity_type = activity_info.get('activity_type_id')
                if activity_type and isinstance(activity_type, list) and len(activity_type) > 1:
                    activity_summary = activity_type[1]
        
        # Buscar selection fields descriptions
        tese_selection_map = await _get_selection_field_mapping(
            odoo_client, 'crm.lead', 'x_studio_tese'
        )
        
        categoria_selection_map = await _get_selection_field_mapping(
            odoo_client, 'res.partner', 'x_studio_categoria_economica'
        )
        
        # Processar dados da oportunidade
        tese_value = str(opp_data.get('x_studio_tese', ''))
        x_studio_tese_desc = tese_selection_map.get(tese_value, tese_value)
        
        categoria_desc = None
        if partner_data:
            categoria_value = str(partner_data.get('x_studio_categoria_economica', ''))
            categoria_desc = categoria_selection_map.get(categoria_value, categoria_value)
        
        processed_opp = {
            'id': opp_data.get('id'),
            'create_date': opp_data.get('create_date'),
            'name': opp_data.get('name'),
            'x_studio_tese': x_studio_tese_desc,
            'partner_id': _extract_relational_name(opp_data.get('partner_id')),
            'user_id': _extract_relational_name(opp_data.get('user_id')),
            'team_id': _extract_relational_name(opp_data.get('team_id')),
            'activity_ids': activity_summary,
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
            'x_studio_usuario_calculo_concluido': _extract_relational_name(opp_data.get('x_studio_usuario_calculo_concluido')),
            'x_studio_categoria_economica': categoria_desc
        }
        
        # Mapear para formato PowerBI com nomes em português
        mapped_opp = _map_to_powerbi_response(processed_opp)
        
        logger.debug(f"Processada oportunidade ID {opportunity_id} com nomes em português para PowerBI (otimizado)")
        return mapped_opp
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar oportunidade ID {opportunity_id} com nomes em português para PowerBI: {str(e)}")
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar dados da oportunidade: {str(e)}"
        )