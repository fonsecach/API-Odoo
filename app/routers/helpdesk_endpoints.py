import logging
from http import HTTPStatus

from fastapi import APIRouter, HTTPException, Query

from app.schemas.schemas import (
    HelpdeskTicketsByVatResponse,
    # HelpdeskTicketUpdate,
)
from app.services.helpdesk_service import (
    # create_ticket,
    # get_helpdesk_info,
    # get_helpdesk_info_by_team_and_id,
    # get_helpdesk_info_by_team_and_stage,
    # get_helpdesk_info_by_team_id,
    get_helpdesk_tickets_by_vat_and_team,
    # update_ticket_team_and_stage,
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix='/tickets', tags=['Central de Ajuda'])


# @router.get('/', summary='Lista todos os chamados abertos')
# async def list_tickets(limit: int = 100, offset: int = 0):
#     """
#     Endpoint para listar todos os chamados de helpdesk de forma assíncrona.

#     Args:
#         limit: Limite de registros a serem retornados
#         offset: Deslocamento para paginação

#     Returns:
#         Lista de chamados encontrados

#     Raises:
#         HTTPException: Se nenhum chamado for encontrado ou houver um erro
#     """
#     helpdesk_info = await get_helpdesk_info(limit, offset)

#     if not helpdesk_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Nenhum chamado localizado',
#         )

#     return {'chamados': helpdesk_info}


# @router.get('/{team_id}', summary='Lista todos os chamados abertos do time')
# async def list_tickets_by_team_id(
#     team_id: int, limit: int = 100, offset: int = 0
# ):
#     """
#     Endpoint para listar chamados filtrados por time de forma assíncrona.

#     Args:
#         team_id: ID do time
#         limit: Limite de registros a serem retornados
#         offset: Deslocamento para paginação

#     Returns:
#         Lista de chamados do time

#     Raises:
#         HTTPException: Se nenhum chamado for encontrado ou houver um erro
#     """
#     helpdesk_info = await get_helpdesk_info_by_team_id(team_id, limit, offset)

#     if not helpdesk_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Nenhum chamado localizado para o time {team_id}',
#         )

#     return {'chamados': helpdesk_info}


# @router.get(
#     '/{team_id}/{ticket_id}',
#     summary='Busca chamado específico pelo ID dentro de um time',
# )
# async def get_ticket_by_team_and_id(team_id: int, ticket_id: int):
#     """
#     Endpoint para buscar um chamado específico dentro de um time de forma assíncrona.

#     Args:
#         team_id: ID do time
#         ticket_id: ID do chamado

#     Returns:
#         Detalhes do chamado encontrado

#     Raises:
#         HTTPException: Se o chamado não for encontrado ou houver um erro
#     """
#     helpdesk_info = await get_helpdesk_info_by_team_and_id(team_id, ticket_id)

#     if not helpdesk_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Chamado {ticket_id} não localizado no time {team_id}',
#         )

#     return {'chamados': helpdesk_info}


# @router.get(
#     '/{team_id}/stage/{stage_id}',
#     summary='Lista todos os chamados do time por estágio',
# )
# async def list_tickets_by_team_and_stage_id(
#     team_id: int, stage_id: int, limit: int = 100, offset: int = 0
# ):
#     """
#     Endpoint para listar chamados de um time filtrados por estágio de forma assíncrona.

#     Args:
#         team_id: ID do time
#         stage_id: ID do estágio
#         limit: Limite de registros a serem retornados
#         offset: Deslocamento para paginação

#     Returns:
#         Lista de chamados do time no estágio especificado

#     Raises:
#         HTTPException: Se nenhum chamado for encontrado ou houver um erro
#     """
#     helpdesk_info = await get_helpdesk_info_by_team_and_stage(
#         team_id, stage_id, limit, offset
#     )

#     if not helpdesk_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Nenhum chamado localizado no estágio {stage_id} para o time {team_id}',
#         )

#     return {'chamados': helpdesk_info}


# @router.patch(
#     '/update',
#     summary='Atualiza o estágio e/ou a equipe de um chamado',
#     response_description='Chamado atualizado com sucesso',
# )
# async def update_ticket_route(update_data: HelpdeskTicketUpdate):
#     """
#     Endpoint para atualizar o estágio e/ou a equipe de um chamado de helpdesk de forma assíncrona.

#     Args:
#         update_data: Dados contendo ticket_id, team_id atual, e opcionalmente new_stage_id e/ou new_team_id

#     Returns:
#         Confirmação da atualização

#     Raises:
#         HTTPException: Se o chamado não for encontrado ou houver um erro
#     """
#     logger.info(
#         f'Recebida requisição para atualizar chamado {update_data.ticket_id}'
#     )

#     # Verificar se o chamado existe na equipe informada
#     ticket = await get_helpdesk_info_by_team_and_id(
#         update_data.team_id, update_data.ticket_id
#     )

#     if not ticket:
#         logger.warning(
#             f'Chamado {update_data.ticket_id} não encontrado na equipe {update_data.team_id}'
#         )
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Chamado {update_data.ticket_id} não encontrado na equipe {update_data.team_id}',
#         )

#     # Obter os valores atuais para o log
#     current_stage_id = (
#         ticket[0]['stage_id'][0]
#         if isinstance(ticket[0]['stage_id'], list)
#         else ticket[0]['stage_id']
#     )
#     current_stage_name = (
#         ticket[0]['stage_id'][1]
#         if isinstance(ticket[0]['stage_id'], list)
#         else 'Unknown'
#     )
#     current_team_id = (
#         ticket[0]['team_id'][0]
#         if isinstance(ticket[0]['team_id'], list)
#         else ticket[0]['team_id']
#     )
#     current_team_name = (
#         ticket[0]['team_id'][1]
#         if isinstance(ticket[0]['team_id'], list)
#         else 'Unknown'
#     )

#     # Atualizar o chamado
#     success = await update_ticket_team_and_stage(
#         update_data.ticket_id,
#         update_data.team_id,
#         update_data.new_stage_id,
#         update_data.new_team_id,
#     )

#     if not success:
#         logger.error(f'Falha ao atualizar chamado {update_data.ticket_id}')
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao atualizar o chamado',
#         )

#     # Preparar mensagem de resposta
#     changes = []
#     if update_data.new_stage_id:
#         changes.append(
#             f'estágio de {current_stage_id} para {update_data.new_stage_id}'
#         )
#     if update_data.new_team_id:
#         changes.append(
#             f'equipe de {current_team_id} para {update_data.new_team_id}'
#         )

#     logger.info(
#         f'Chamado {update_data.ticket_id} atualizado: {", ".join(changes)}'
#     )

#     # Preparar detalhes da resposta
#     response = {
#         'message': 'Chamado atualizado com sucesso',
#         'ticket_id': update_data.ticket_id,
#         'changes': [],
#     }

#     if update_data.new_stage_id:
#         response['changes'].append({
#             'field': 'stage_id',
#             'old_value': {'id': current_stage_id, 'name': current_stage_name},
#             'new_value': {'id': update_data.new_stage_id},
#         })

#     if update_data.new_team_id:
#         response['changes'].append({
#             'field': 'team_id',
#             'old_value': {'id': current_team_id, 'name': current_team_name},
#             'new_value': {'id': update_data.new_team_id},
#         })

#     return response


# class HelpdeskTicketCreate(BaseModel):
#     """Modelo para criação de chamados de helpdesk."""

#     name: str
#     team_id: int
#     description: str = ''
#     partner_id: int = None
#     user_id: int = None
#     priority: str = '0'


# @router.post(
#     '/',
#     summary='Cria um novo chamado de helpdesk',
#     status_code=HTTPStatus.CREATED,
# )
# async def create_helpdesk_ticket(
#     ticket_data: HelpdeskTicketCreate, request: Request
# ):
#     """
#     Endpoint para criar um novo chamado de helpdesk de forma assíncrona.

#     Args:
#         ticket_data: Dados do chamado a ser criado
#         request: Objeto de requisição para identificação do cliente

#     Returns:
#         Confirmação da criação com ID do chamado

#     Raises:
#         HTTPException: Se houver um erro na criação
#     """
#     client_ip = request.client.host
#     logger.info(
#         f"Requisição para criar chamado '{ticket_data.name}' recebida de {client_ip}"
#     )

#     # Criar o chamado
#     ticket_id = await create_ticket(ticket_data.dict())

#     if not ticket_id:
#         logger.error(f"Falha ao criar chamado '{ticket_data.name}'")
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao criar o chamado',
#         )

#     logger.info(
#         f"Chamado '{ticket_data.name}' criado com sucesso, ID: {ticket_id}"
#     )

#     return {
#         'message': 'Chamado criado com sucesso',
#         'ticket_id': ticket_id,
#         'name': ticket_data.name,
#         'team_id': ticket_data.team_id,
#     }


@router.get(
    '/client-vat/{vat}/team/1',
    summary='Lista chamados de um cliente (por CNPJ/VAT) na equipe de Helpdesk 1',
    response_model=HelpdeskTicketsByVatResponse
)
async def list_tickets_by_vat_for_team_1(
    vat: str,
    limit: int = Query(
        100, description='Limite de registros a serem retornados'
    ),
    offset: int = Query(0, description='Deslocamento para paginação'),
):
    """
    Endpoint para listar chamados de helpdesk para um cliente específico (identificado por VAT/CNPJ)
    dentro da equipe de Helpdesk com ID 1.

    Args:
        vat: CNPJ do cliente.
        limit: Limite de registros a serem retornados.
        offset: Deslocamento para paginação.

    Returns:
        Lista de chamados do cliente na equipe 1.

    Raises:
        HTTPException: Se o VAT for inválido, nenhum chamado for encontrado, ou ocorrer um erro interno.
    """
    team_id_fixed = 1  # As per requirement, team_id is 1
    try:
        tickets = await get_helpdesk_tickets_by_vat_and_team(
            vat=vat, team_id=team_id_fixed, limit=limit, offset=offset
        )

        if (
            not tickets
        ):  # tickets will be an empty list if none are found by the service
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f'Nenhum chamado encontrado para o VAT {vat} na equipe {team_id_fixed}',
            )
        return {'chamados': tickets}
    except ValueError as e:  # Catch VAT validation errors specifically
        logger.error(f"Erro de valor ao buscar chamados por VAT '{vat}': {e}")
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))
    except (
        HTTPException
    ):  # Re-raise HTTPExceptions that might come from deeper calls if any
        raise
    except Exception as e:
        logger.error(
            f"Erro inesperado ao listar chamados por VAT '{vat}' na equipe {team_id_fixed}: {str(e)}"
        )
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro interno ao processar a solicitação de chamados por VAT: {str(e)}',
        )
