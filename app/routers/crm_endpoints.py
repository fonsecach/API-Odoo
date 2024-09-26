from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.Services.authentication import connect_to_odoo, authenticate_odoo
from app.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD

router = APIRouter()


@router.get("/opportunities", summary="Lista oportunidades cadastradas")
async def list_opportunities(limit: int = 100, offset: int = 0):

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    from app.Services.crm_service import get_opportunities_info
    opportunities_info = get_opportunities_info(models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset)

    if not opportunities_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma oportunidade localizada')

    return {"opportunities": opportunities_info}


@router.get("/opportunities/{opportunity_id}", summary="Oportunidade pelo ID")
async def get_opportunity_by_id(opportunity_id: int):

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    from app.Services.crm_service import get_opportunity_by_id
    opportunity_info = get_opportunity_by_id(models, ODOO_DB, uid, ODOO_PASSWORD, opportunity_id)

    if not opportunity_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma oportunidade localizada')

    return {"opportunity": opportunity_info}

