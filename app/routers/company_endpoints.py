from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import Company_default, Company_return, Message
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.company_service import (
    create_company_in_odoo,
    delete_company_in_odoo,
    get_clients_info,
    get_companies_info,
    get_company_by_id,
    get_company_by_vat,
    update_company_in_odoo,
)
from app.utils.utils import clean_vat

router = APIRouter()


@router.get('/clients', summary='Lista clientes cadastrados')
async def list_clients(limit: int = 100, offset=0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    clients_info = get_clients_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not clients_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhum cliente localizado',
        )

    return {'clients': clients_info}


@router.get('/companies', summary='Lista empresas cadastradas')
async def list_companies(limit: int = 100, offset=0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    companies_info = get_companies_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'total_companies': len(companies_info),
        'companies': companies_info,
    }


@router.get(
    '/companies/by_vat', summary='Lista empresas cadastradas pelo CNPJ'
)
async def list_companies_by_vat(vat: str):
    try:
        vat = clean_vat(vat)
    except ValueError as e:
        raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=str(e))

    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    companies_info = get_company_by_vat(
        vat, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'total_companies': len(companies_info),
        'companies': companies_info,
    }


@router.get('/companies/by_id', summary='Lista empresas cadastradas pelo ID')
async def list_companies_by_id(id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    companies_info = get_company_by_id(id, models, ODOO_DB, uid, ODOO_PASSWORD)

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'total_companies': len(companies_info),
        'companies': companies_info,
    }


from fastapi import status


@router.post(
    '/companies',
    summary='Cadastrar uma empresa',
    status_code=status.HTTP_201_CREATED,
    response_model=Company_return,
)
async def create_company(company_info: Company_default):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    existing_companies = models.execute_kw(
        ODOO_DB,
        uid,
        ODOO_PASSWORD,
        'res.partner',
        'search_read',
        [[['vat', '=', company_info.vat]]],
        {'fields': ['id', 'name', 'vat'], 'limit': 1},
    )

    if existing_companies:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f'Empresa com VAT {company_info.vat} já está cadastrada',
        )

    company_id = create_company_in_odoo(
        company_info.dict(), models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not company_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail='Nenhuma empresa criada'
        )

    return {
        'company_id': company_id,
        'name': company_info.name,
        'vat': company_info.vat,
        'country_id': company_info.country_id,
        'phone': company_info.phone,
        'email': company_info.email,
    }


@router.put(
    '/companies/{company_id}',
    summary='Atualizar uma empresa',
    status_code=status.HTTP_200_OK,
)
async def update_company(company_id: int, company_info: Company_default):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    success = update_company_in_odoo(
        company_id, company_info.dict(), models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not success:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa atualizada',
        )

    return {'company_id': company_id}


@router.delete(
    '/companies',
    summary='Excluir uma empresa',
    status_code=status.HTTP_200_OK,
    response_model=Message,
)
async def delete_company(company_id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    company_id = delete_company_in_odoo(
        company_id, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not company_id:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa excluída',
        )

    return {'message': 'User deleted'}
