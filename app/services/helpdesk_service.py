import logging
from typing import Any, Dict, List, Optional

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.services.async_odoo_client import AsyncOdooClient
from app.services.company_service import (
    get_company_by_vat,
)
from app.utils.utils import clean_vat

# Configurar logging
logger = logging.getLogger(__name__)

# Constantes
HELPDESK_TICKET_MODEL = 'helpdesk.ticket'
HELPDESK_DEFAULT_FIELDS = [
    'id',
    'name',
    'team_id',
    'stage_id',
    'user_id',
    'partner_id',
    'priority',
    'description',
]


async def get_odoo_client() -> AsyncOdooClient:
    """
    Obtém uma instância do cliente Odoo assíncrono.
    Reutiliza conexões existentes quando possível.
    """
    return await AsyncOdooClient.get_instance(
        ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
    )


async def get_helpdesk_info(
    limit: int = 100, offset: int = 0, fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Obtém informações de chamados de helpdesk de forma assíncrona.

    Args:
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        fields: Campos específicos a serem retornados (usa padrão se None)

    Returns:
        Lista de chamados ou lista vazia em caso de erro
    """
    client = await get_odoo_client()

    if fields is None:
        fields = HELPDESK_DEFAULT_FIELDS

    try:
        return await client.search_read(
            HELPDESK_TICKET_MODEL,
            [],
            fields=fields,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f'Erro ao buscar e ler informações dos tickets: {e}')
        return []


async def get_helpdesk_info_by_team_id(
    team_id: int,
    limit: int = 100,
    offset: int = 0,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Obtém chamados de helpdesk filtrados por time de forma assíncrona.

    Args:
        team_id: ID do time
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        fields: Campos específicos a serem retornados (usa padrão se None)

    Returns:
        Lista de chamados do time ou lista vazia em caso de erro
    """
    client = await get_odoo_client()

    if fields is None:
        fields = HELPDESK_DEFAULT_FIELDS

    try:
        return await client.search_read(
            HELPDESK_TICKET_MODEL,
            [['team_id', '=', team_id]],
            fields=fields,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(f'Erro ao buscar chamados do time {team_id}: {e}')
        return []


async def get_helpdesk_info_by_team_and_id(
    team_id: int, ticket_id: int, fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Obtém um chamado específico de um time de forma assíncrona.

    Args:
        team_id: ID do time
        ticket_id: ID do chamado
        fields: Campos específicos a serem retornados (usa padrão se None)

    Returns:
        Lista com o chamado correspondente ou lista vazia se não encontrado
    """
    client = await get_odoo_client()

    if fields is None:
        fields = HELPDESK_DEFAULT_FIELDS

    try:
        return await client.search_read(
            HELPDESK_TICKET_MODEL,
            [['team_id', '=', team_id], ['id', '=', ticket_id]],
            fields=fields,
        )
    except Exception as e:
        logger.error(
            f'Erro ao buscar chamado {ticket_id} do time {team_id}: {e}'
        )
        return []


async def get_helpdesk_info_by_team_and_stage(
    team_id: int,
    stage_id: int,
    limit: int = 100,
    offset: int = 0,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Obtém chamados de um time filtrados por estágio de forma assíncrona.

    Args:
        team_id: ID do time
        stage_id: ID do estágio
        limit: Limite de registros a serem retornados
        offset: Deslocamento para paginação
        fields: Campos específicos a serem retornados (usa padrão se None)

    Returns:
        Lista de chamados do time no estágio especificado ou lista vazia em caso de erro
    """
    client = await get_odoo_client()

    if fields is None:
        fields = HELPDESK_DEFAULT_FIELDS

    try:
        return await client.search_read(
            HELPDESK_TICKET_MODEL,
            [['team_id', '=', team_id], ['stage_id', '=', stage_id]],
            fields=fields,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        logger.error(
            f'Erro ao buscar chamados do time {team_id} no estágio {stage_id}: {e}'
        )
        return []


async def update_ticket_team_and_stage(
    ticket_id: int,
    current_team_id: int,
    new_stage_id: Optional[int] = None,
    new_team_id: Optional[int] = None,
) -> bool:
    """
    Atualiza o estágio e/ou a equipe de um chamado de helpdesk de forma assíncrona.

    Args:
        ticket_id: ID do chamado a ser atualizado
        current_team_id: ID da equipe atual do chamado (para validação)
        new_stage_id: ID do novo estágio (opcional)
        new_team_id: ID da nova equipe (opcional)

    Returns:
        True se bem-sucedido, False se falhar
    """
    if new_stage_id is None and new_team_id is None:
        logger.warning(
            'Nenhuma atualização solicitada (estágio e equipe são None)'
        )
        return False

    client = await get_odoo_client()

    try:
        # Verificar se o chamado existe e pertence à equipe informada
        tickets = await client.search_read(
            HELPDESK_TICKET_MODEL,
            [['id', '=', ticket_id], ['team_id', '=', current_team_id]],
            fields=['id', 'stage_id', 'team_id'],
        )

        if not tickets:
            logger.warning(
                f'Chamado {ticket_id} não encontrado ou não pertence à equipe {current_team_id}'
            )
            return False

        # Preparar dados para atualização
        update_data = {}
        if new_stage_id is not None:
            update_data['stage_id'] = new_stage_id
        if new_team_id is not None:
            update_data['team_id'] = new_team_id

        # Atualizar o chamado
        result = await client.write(
            HELPDESK_TICKET_MODEL, ticket_id, update_data
        )

        if result:
            updates = []
            if new_stage_id is not None:
                updates.append(f'estágio para {new_stage_id}')
            if new_team_id is not None:
                updates.append(f'equipe para {new_team_id}')

            logger.info(
                f'Chamado {ticket_id} atualizado: {", ".join(updates)}'
            )
        else:
            logger.warning(f'Falha ao atualizar chamado {ticket_id}')

        return result
    except Exception as e:
        logger.error(f'Erro ao atualizar chamado {ticket_id}: {e}')
        return False


async def create_ticket(ticket_data: Dict[str, Any]) -> Optional[int]:
    """
    Cria um novo chamado de helpdesk de forma assíncrona.

    Args:
        ticket_data: Dados do chamado a ser criado

    Returns:
        ID do chamado criado ou None em caso de erro
    """
    client = await get_odoo_client()

    try:
        # Campos obrigatórios
        if 'name' not in ticket_data or 'team_id' not in ticket_data:
            logger.error(
                "Campos obrigatórios 'name' e 'team_id' não fornecidos"
            )
            return None

        # Criar o chamado
        ticket_id = await client.create(HELPDESK_TICKET_MODEL, ticket_data)

        if ticket_id:
            logger.info(
                f"Chamado '{ticket_data['name']}' criado com sucesso, ID: {ticket_id}"
            )
        else:
            logger.warning('Falha ao criar chamado')

        return ticket_id
    except Exception as e:
        logger.error(f'Erro ao criar chamado: {e}')
        return None


async def update_ticket(ticket_id: int, ticket_data: Dict[str, Any]) -> bool:
    """
    Atualiza um chamado existente de forma assíncrona.

    Args:
        ticket_id: ID do chamado a ser atualizado
        ticket_data: Dados a serem atualizados

    Returns:
        True se bem-sucedido, False se falhar
    """
    client = await get_odoo_client()

    try:
        # Verificar se o chamado existe
        ticket_exists = await client.search_read(
            HELPDESK_TICKET_MODEL, [['id', '=', ticket_id]], fields=['id']
        )

        if not ticket_exists:
            logger.warning(f'Chamado {ticket_id} não encontrado')
            return False

        # Atualizar o chamado
        result = await client.write(
            HELPDESK_TICKET_MODEL, ticket_id, ticket_data
        )

        if result:
            logger.info(f'Chamado {ticket_id} atualizado com sucesso')
        else:
            logger.warning(f'Falha ao atualizar chamado {ticket_id}')

        return result
    except Exception as e:
        logger.error(f'Erro ao atualizar chamado {ticket_id}: {e}')
        return False


async def get_helpdesk_tickets_by_vat_and_team(
    vat: str, team_id: int, limit: int = 100, offset: int = 0
) -> List[Dict[str, Any]]:
    """
    Obtém chamados de helpdesk de um cliente (por VAT) em uma equipe específica.

    Args:
        vat: CNPJ/VAT do cliente.
        team_id: ID da equipe de helpdesk.
        limit: Limite de registros a serem retornados.
        offset: Deslocamento para paginação.

    Returns:
        Lista de chamados formatados ou lista vazia em caso de erro/não encontrado.
    """
    client = await get_odoo_client()
    cleaned_vat: str
    try:
        cleaned_vat = clean_vat(vat)
    except ValueError as e:
        logger.error(f'Formato de VAT inválido: {vat} - {e}')
        raise ValueError(f'Formato de VAT inválido: {vat}. Detalhe: {str(e)}')

    partners_info = await get_company_by_vat(cleaned_vat, fields=['id'])
    if not partners_info:
        logger.info(f'Nenhuma empresa encontrada para o VAT: {cleaned_vat}')
        return []

    partner_ids = [p['id'] for p in partners_info if 'id' in p]
    if not partner_ids:
        logger.info(
            f'Nenhum ID de parceiro extraído para o VAT: {cleaned_vat}'
        )
        return []

    fields_to_fetch = [
        'id',
        'name',
        'partner_id',
        'stage_id',
        'write_date',
        'date_last_stage_update',
    ]

    domain = [
        ['team_id', '=', team_id],
        ['partner_id', 'in', partner_ids],
    ]

    try:
        tickets_data = await client.search_read(
            HELPDESK_TICKET_MODEL,
            domain,
            fields=fields_to_fetch,
            limit=limit,
            offset=offset,
            order='create_date desc',
        )

        formatted_tickets = []
        for ticket in tickets_data:
            client_name = None
            if (
                ticket.get('partner_id')
                and isinstance(ticket['partner_id'], list)
                and len(ticket['partner_id']) > 1
            ):
                client_name = ticket['partner_id'][1]
            elif ticket.get('partner_id') and isinstance(
                ticket.get('partner_id'), str
            ): 
                client_name = ticket.get('partner_id')

            stage_name = None
            if (
                ticket.get('stage_id')
                and isinstance(ticket['stage_id'], list)
                and len(ticket['stage_id']) > 1
            ):
                stage_name = ticket['stage_id'][1]
            elif ticket.get('stage_id') and isinstance(
                ticket.get('stage_id'), str
            ):
                stage_name = ticket.get('stage_id')

            formatted_ticket = {
                'id': ticket['id'],
                'name': ticket.get('name'),
                'client_name': client_name,
                'stage_name': stage_name,
                'write_date': ticket.get('write_date'),
                'date_last_stage_update': ticket.get('date_last_stage_update'),
            }
            formatted_tickets.append(formatted_ticket)
        return formatted_tickets
    except Exception as e:
        logger.error(
            f'Erro ao buscar chamados de helpdesk por VAT ({vat}) e equipe ({team_id}): {e}'
        )
        raise Exception(f'Erro ao processar chamados por VAT: {str(e)}')
