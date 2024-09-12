from http import HTTPStatus
from fastapi import APIRouter, HTTPException

from src.models.models import Company_default
from src.odoo_connector.authentication import connect_to_odoo, authenticate_odoo
from src.odoo_connector.company_service import get_companies_info, get_company_by_vat, get_company_by_id, \
    create_company_in_odoo
from src.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
from src.utils.utils import clean_vat

router = APIRouter()

@router.get("/companies", summary="Lista empresas cadastradas")
async def list_companies(limit: int = 100):

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    companies_info = get_companies_info(models, ODOO_DB, uid, ODOO_PASSWORD, limit)

    if not companies_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa localizada')

    return {"total_companies": len(companies_info), "companies": companies_info}


@router.get("/companies/by_vat", summary="Lista empresas cadastradas pelo CNPJ")
async def list_companies_by_vat(vat: str):

    try:
        vat = clean_vat(vat)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    companies_info = get_company_by_vat(vat, models, ODOO_DB, uid, ODOO_PASSWORD)

    if not companies_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa localizada')

    return {"total_companies": len(companies_info), "companies": companies_info}


@router.get("/companies/by_id", summary="Lista empresas cadastradas pelo ID")
async def list_companies_by_id(id: int):

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    companies_info = get_company_by_id(id, models, ODOO_DB, uid, ODOO_PASSWORD)

    if not companies_info:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa localizada')

    return {"total_companies": len(companies_info), "companies": companies_info}

from fastapi import HTTPException, status
from http import HTTPStatus


@router.post("/companies", summary="Cadastrar uma empresa", status_code=status.HTTP_201_CREATED, response_model=Company_default)
async def create_company(company_info: Company_default):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    company_id = create_company_in_odoo(company_info.dict(), models, ODOO_DB, uid, ODOO_PASSWORD)

    if not company_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa criada')

    return {"company_id": company_id}
