from http import HTTPStatus

from fastapi import APIRouter, HTTPException, status

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import Opportunity_default, Opportunity_return
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.company_service import get_or_create_partner
from app.Services.crm_service import (
    create_opportunity_in_crm,
    fetch_opportunity_by_id,
    get_opportunities_info,
)

router = APIRouter(prefix='/opportunities', tags=['Oportunidades'])


@router.get('/', summary='Lista oportunidades cadastradas')
async def list_opportunities(limit: int = 100, offset: int = 0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    opportunities_info = get_opportunities_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not opportunities_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade localizada',
        )

    return {'opportunities': opportunities_info}


@router.get('/{opportunity_id}', summary='Oportunidade pelo ID')
async def get_opportunity_by_id(opportunity_id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )
    opportunity_info = fetch_opportunity_by_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, opportunity_id
    )
    if not opportunity_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade localizada',
        )
    return {'opportunity': opportunity_info}


@router.post(
    '/',
    summary='Cadastrar uma oportunidade',
    status_code=status.HTTP_201_CREATED,
    response_model=Opportunity_return,
)
async def create_opportunity(opportunity_info: Opportunity_default):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    # 🔹 Passo 1: Criar cliente a partir do contato
    partner_id = get_or_create_partner(
        opportunity_info.contact_name, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not partner_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Erro ao criar ou recuperar o cliente',
        )

    # 🔹 Passo 2: Criar oportunidade no CRM
    opportunity_data = opportunity_info.dict(exclude_unset=True)
    opportunity_data.update({
        'partner_id': partner_id,  # Associar cliente
        'type': 'opportunity',  # Definir como oportunidade (não lead)
    })

    opportunity_id = create_opportunity_in_crm(
        opportunity_data, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not opportunity_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma oportunidade criada',
        )

    return {'opportunity_id': opportunity_id, **opportunity_data}
