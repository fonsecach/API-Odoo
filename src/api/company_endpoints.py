from fastapi import APIRouter, HTTPException
from src.odoo_connector.authentication import connect_to_odoo, authenticate_odoo
from src.odoo_connector.company_service import get_companies_info
from src.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD

router = APIRouter()

@router.get("/companies", summary="Lista empresas cadastradas")
async def list_companies(limit: int = 5):
    """Retorna uma lista das empresas cadastradas, limitada pelo parâmetro limit."""

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=401, detail="Falha na autenticação no Odoo")

    companies_info = get_companies_info(models, ODOO_DB, uid, ODOO_PASSWORD, limit)

    if not companies_info:
        return {"message": "Nenhuma empresa encontrada"}

    return {"total_companies": len(companies_info), "companies": companies_info}
