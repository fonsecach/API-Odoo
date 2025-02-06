from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import Company_default, Company_return, Message, contact_update
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.company_service import (
    create_company_in_odoo,
    delete_company_in_odoo,
    fetch_client_by_complete_name,
    get_clients_info,
    get_company_by_id,
    get_company_by_vat,
    update_company_in_odoo,
)
from app.utils.utils import clean_vat

router = APIRouter(prefix='/company', tags=['company'])


@router.get('/', summary='Lista empresas cadastradas')
async def list_companies(limit: int = 100, offset=0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    companies_info = get_clients_info(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'companies': companies_info,
    }


@router.get('/vat', summary='Lista empresa por CNPJ')
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
        'companies': companies_info,
    }


@router.get('/name', summary='Retorna o cliente pelo nome da empresa')
async def get_client_by_complete_name(name: str):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    companies_info = fetch_client_by_complete_name(
        name, models, ODOO_DB, uid, ODOO_PASSWORD
    )

    if not companies_info:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma empresa localizada',
        )

    return {
        'client': companies_info,
    }


@router.get('/id', summary='Lista empresas cadastradas pelo ID')
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
        'companies': companies_info,
    }


from fastapi import status


@router.post(
    '/',
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
    '/{id}',
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
    '/',
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


@router.patch('/{id}',
              summary='Atualizar o cnpj e segmento do cliente',
              response_description='Cliente atualizado com sucesso!')
async def update_client_fields(
    id: int,
    contact_update: contact_update,
):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    
    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )
        
    contact_info = get_company_by_id(id, models, ODOO_DB, uid, ODOO_PASSWORD)
    
    #Atualiza os campos no odoo
    try:
        models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            'res.partner',
            'write',
            [
                [id],
                {
                    'x_studio_categoria_economica': contact_update.x_studio_categoria_economica,
                    'vat': contact_update.vat,
                    'company_type': contact_update.company_type,
                },
            ],
        )
        return {
            'message': 'Cliente atualizado com sucesso!',
            'updated_fields': {
                'x_studio_categoria_economica': contact_update.x_studio_categoria_economica,
                'vat': contact_update.vat,
                'company_type': contact_update.company_type
            },
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Falha ao atualizar o cliente: {str(e)}',
        )
        