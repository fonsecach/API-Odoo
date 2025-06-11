# from http import HTTPStatus

# from fastapi import APIRouter, HTTPException

# from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
# from app.schemas.schemas import SaleOrderCreate, SaleOrderUpdate
# from app.services.authentication import authenticate_odoo, connect_to_odoo
# from app.services.sales_orders import (
#     SalesOrderService,
#     get_sales_order_by_id,
#     get_sales_orders,
#     search_sales_orders_by_name,
#     update_sales_order_fields,
# )

# router = APIRouter(prefix='/sales_orders', tags=['Pedidos de venda'])


# @router.get('/', summary='Lista pedidos de venda cadastrados')
# async def list_sales_orders(limit: int = 100, offset: int = 0):
#     # Endpoint para listar todos os pedidos de venda com paginação.
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     sales_orders_info = get_sales_orders(
#         models, ODOO_DB, uid, ODOO_PASSWORD, limit, offset
#     )

#     if not sales_orders_info:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail='Nenhum pedido de venda localizado',
#         )

#     return {'sales_orders': sales_orders_info}


# @router.get('/{order_id}', summary='Busca pedido de venda por ID')
# async def get_order_by_id(order_id: int):
#     # Endpoint para buscar um pedido de venda específico pelo ID.

#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     sales_order = get_sales_order_by_id(
#         models, ODOO_DB, uid, ODOO_PASSWORD, order_id
#     )

#     if not sales_order:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Pedido de venda com ID {order_id} não encontrado',
#         )

#     return {'sales_order': sales_order}


# @router.get('/search/', summary='Busca pedidos de venda por nome')
# async def search_orders_by_name(name: str, limit: int = 100, offset: int = 0):
#     # Endpoint para buscar pedidos de venda pelo nome ou nome do cliente.

#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     sales_orders = search_sales_orders_by_name(
#         models, ODOO_DB, uid, ODOO_PASSWORD, name, limit, offset
#     )

#     if not sales_orders:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Nenhum pedido de venda encontrado com o nome contendo "{name}"',
#         )

#     return {'sales_orders': sales_orders}


# @router.post(
#     '/', summary='Cria um novo pedido de venda', status_code=HTTPStatus.CREATED
# )
# async def create_sales_order(order: SaleOrderCreate):
#     """
#     Endpoint para criar um novo pedido de venda no Odoo.

#     Recebe os dados do pedido, valida campos obrigatórios e opcionalmente
#     vincula a uma oportunidade existente.
#     """
#     try:
#         # Converte o schema Pydantic para um dicionário
#         order_data = order.dict(exclude_unset=True)

#         # Verifica campos obrigatórios
#         if not order_data.get('partner_id'):
#             raise HTTPException(
#                 status_code=HTTPStatus.BAD_REQUEST,
#                 detail='O campo partner_id é obrigatório',
#             )

#         if (
#             not order_data.get('order_line')
#             or len(order_data['order_line']) == 0
#         ):
#             raise HTTPException(
#                 status_code=HTTPStatus.BAD_REQUEST,
#                 detail='É necessário pelo menos um item na linha de pedido',
#             )

#         # Chama o serviço para criar o pedido de venda
#         order_id = SalesOrderService.create_sales_order(order_data)

#         response = {
#             'order_id': order_id,
#             'status': 'success',
#             'message': 'Pedido de venda criado com sucesso',
#         }

#         if order_data.get('opportunity_id'):
#             response['opportunity_id'] = order_data['opportunity_id']
#             response['message'] += ' e vinculado à oportunidade'

#         return response

#     except ValueError as e:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail=str(e),
#         )
#     except Exception as e:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail=f'Erro interno ao processar a requisição: {str(e)}',
#         )


# @router.patch(
#     '/{order_id}',
#     summary='Atualiza campos específicos de um pedido de venda',
#     response_description='Campos atualizados com sucesso',
# )
# async def update_sales_order_fields_route(
#     order_id: int,
#     order_update: SaleOrderUpdate,
# ):
#     """
#     Endpoint para atualizar user_id e/ou type_name de um pedido de venda.
#     :param order_id: ID do pedido a ser atualizado
#     :param order_update: Dados para atualização (user_id e/ou type_name)
#     """
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autenticação no Odoo',
#         )

#     order = get_sales_order_by_id(
#         models, ODOO_DB, uid, ODOO_PASSWORD, order_id
#     )

#     if not order:
#         raise HTTPException(
#             status_code=HTTPStatus.NOT_FOUND,
#             detail=f'Pedido de venda com ID {order_id} não encontrado',
#         )

#     fields_data = {}
#     if order_update.user_id is not None:
#         fields_data['user_id'] = order_update.user_id
#     if order_update.type_name is not None:
#         fields_data['type_name'] = order_update.type_name

#     # Se não há campos para atualizar, retorna erro
#     if not fields_data:
#         raise HTTPException(
#             status_code=HTTPStatus.BAD_REQUEST,
#             detail='Nenhum campo fornecido para atualização',
#         )

#     success = update_sales_order_fields(
#         models, ODOO_DB, uid, ODOO_PASSWORD, order_id, fields_data
#     )

#     if not success:
#         raise HTTPException(
#             status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
#             detail='Falha ao atualizar o pedido de venda',
#         )

#     return {
#         'message': 'Campos do pedido de venda atualizados com sucesso',
#         'order_id': order_id,
#         'updated_fields': fields_data,
#     }
