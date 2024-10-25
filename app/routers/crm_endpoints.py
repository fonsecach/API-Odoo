from http import HTTPStatus

from fastapi import APIRouter, HTTPException, status

from app.Services.authentication import connect_to_odoo, authenticate_odoo
from app.Services.crm_service import create_opportunity_in_crm
from app.config.settings import ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD
from app.schemas.schemas import Opportunity_return, Opportunity_default

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


@router.post('/opportunities', summary="Cadastrar uma oportunidade", status_code=status.HTTP_201_CREATED,
             response_model=Opportunity_return)
async def create_opportunity(opportunity_info: Opportunity_default):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Falha na autenticação no Odoo")

    # Verificar se já existe uma oportunidade para o cliente e o produto (tese)
    existing_opportunity = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'crm.lead', 'search_read',
        [[
            ['partner_id', '=', opportunity_info.partner_id],
            ['x_studio_tese', '=', opportunity_info.x_studio_tese]
        ]],
        {'fields': ['id'], 'limit': 1}
    )

    if existing_opportunity:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST,
                            detail=f"Oportunidade já cadastrada para o cliente {opportunity_info.partner_id}")

    opportunity_id = create_opportunity_in_crm(opportunity_info.dict(), models, ODOO_DB, uid, ODOO_PASSWORD)

    if not opportunity_id:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma oportunidade criada')

    return {
        "opportunity_id": opportunity_id,
        "name": opportunity_info.name,
        "partner_id": opportunity_info.partner_id,
        "x_studio_tese": opportunity_info.x_studio_tese,
        "stage_id": opportunity_info.stage_id,
        "user_id": opportunity_info.user_id,
        'x_studio_omie_id': opportunity_info.x_studio_omie_id
        #'x_studio_criao_no_omie': opportunity_info.x_studio_criao_no_omie
    }



