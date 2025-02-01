from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.Services.authentication import authenticate_odoo, connect_to_odoo
from app.Services.sales_orders import get_sales_orders


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