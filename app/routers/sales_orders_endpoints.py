from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.schemas.schemas import SaleOrderCreate
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.sales_orders import (
    SalesOrderService,
    get_sales_order_by_id,
    get_sales_orders,
    search_sales_orders_by_name,
)

router = APIRouter(prefix='/sales_orders', tags=['Pedidos de venda'])


@router.get('/', summary='Lista pedidos de venda cadastrados')
async def list_sales_orders(limit: int = 100, offset: int = 0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    sales_orders_info = get_sales_orders(
        models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
    )

    if not sales_orders_info:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Nenhum pedido de venda localizado',
        )

    return {'sales_orders': sales_orders_info}


@router.get('/{order_id}', summary='Busca pedido de venda por ID')
async def get_order_by_id(order_id: int):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    sales_order = get_sales_order_by_id(
        models, ODOO_DB, uid, ODOO_PASSWORD, order_id
    )

    if not sales_order:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Pedido de venda com ID {order_id} não encontrado',
        )

    return {'sales_order': sales_order}


@router.get('/search/', summary='Busca pedidos de venda por nome')
async def search_orders_by_name(name: str, limit: int = 100, offset: int = 0):
    common, models = connect_to_odoo(ODOO_URL)
    uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

    if not uid:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Falha na autenticação no Odoo',
        )

    sales_orders = search_sales_orders_by_name(
        models, ODOO_DB, uid, ODOO_PASSWORD, name, limit, offset
    )

    if not sales_orders:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f'Nenhum pedido de venda encontrado com o nome contendo "{name}"',
        )

    return {'sales_orders': sales_orders}


@router.post('/', summary='Cria um novo pedido de venda', status_code=HTTPStatus.CREATED)
async def create_sales_order(order: SaleOrderCreate):
    try:
        # Converte o schema Pydantic para um dicionário
        order_data = order.dict()

        # Chama o serviço para criar o pedido de venda
        order_id = SalesOrderService.create_sales_order(order_data)

        return {'order_id': order_id}

    except ValueError as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar a requisição: {str(e)}",
        )
