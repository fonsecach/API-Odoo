from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.services.authentication import authenticate_odoo, connect_to_odoo
from app.services.helpdesk_service import (
    get_helpdesk_info,
    get_helpdesk_info_by_team_and_id,
    get_helpdesk_info_by_team_id,
)

router = APIRouter(prefix='/tickets', tags=['Central de Ajuda'])


@router.get('/', summary='Lista todos os chamados abertos')
async def list_tickets(limit: int = 100, offset: int = 0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autentificação no Odoo',
        )

    helpdesk_info = get_helpdesk_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not helpdesk_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhum chamado localizado',
        )

    return {'chamados': helpdesk_info}


@router.get('/{team_id}', summary='Lista todos os chamados abertos do time')
async def list_tickets_by_team_id(
    team_id: int, limit: int = 100, offset: int = 0
):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autentificação no Odoo',
        )

    helpdesk_info = get_helpdesk_info_by_team_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, team_id, limit, offset
    )

    if not helpdesk_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhum chamado localizado',
        )

    return {'chamados': helpdesk_info}


@router.get(
    '/{team_id}/{ticket_id}',
    summary='Lista todos os chamados abertos do time',
)
async def list_tickets_by_team_id(team_id: int, ticket_id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autentificação no Odoo',
        )

    helpdesk_info = get_helpdesk_info_by_team_and_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, team_id, ticket_id
    )

    if not helpdesk_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhum chamado localizado',
        )

    return {'chamados': helpdesk_info}


@router.get(
    '/{team_id}/{stage_id}',
    summary='Lista todos os chamados abertos do time por estágio',
)
async def list_tickets_by_team_and_stage_id(
    team_id: int, stage_id: int, limit: int = 100, offset: int = 0
):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autentificação no Odoo',
        )

    helpdesk_info = get_helpdesk_info_by_team_and_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, team_id, stage_id, limit, offset
    )

    if not helpdesk_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhum chamado localizado',
        )

    return {'chamados': helpdesk_info}
