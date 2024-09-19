from http import HTTPStatus
from fastapi import APIRouter, HTTPException

from src.models.models import Company_default, Company_return, Message
from src.odoo_connector.authentication import connect_to_odoo, authenticate_odoo
from src.odoo_connector.company_service import get_companies_info, get_company_by_vat, get_company_by_id, \
    create_company_in_odoo, delete_company_in_odoo, update_company_in_odoo, get_clients_info
from src.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
from src.utils.utils import clean_vat


router = APIRouter()


@router.get("/opportunities", summary="Lista oportunidades cadastradas")
async def list_opportunities(limit: int = 100):

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    clients_info = get_clients_info(models, ODOO_DB, uid, ODOO_PASSWORD, limit)

    if not clients_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhum cliente localizado')

    return { "clients": clients_info}

