from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import PartnerNames
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.migracao import get_partners_by_names

router = APIRouter(prefix='/partners', tags=['Migração'])


@router.post('/search')
async def search_partners(partner_names: PartnerNames):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    partners = get_partners_by_names(
        partner_names.names, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not partners:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Nenhuma empresa encontrada',
        )

    return {
        'partners': [
            {'name': name, 'id': partner_id}
            for name, partner_id in partners.items()
        ]
    }
