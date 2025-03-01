from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict

from fastapi import HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.Services.authentication import authenticate_odoo, connect_to_odoo


def get_sales_orders(models, db, uid, password, limit=100, offset=0):
    try:
        sales_order_info = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'search_read',
            [[]],
            {'limit': limit, 'offset': offset},
        )
        return sales_order_info
    except Exception as e:
        print(f'Erro ao buscar as informaçoões dos pedidos de venda: {e}')
        return []


def get_sales_order_by_id(models, db, uid, password, order_id):
    try:
        sales_order = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'search_read',
            [[['id', '=', order_id]]],
            {'limit': 1},
        )
        return sales_order[0] if sales_order else None
    except Exception as e:
        print(f'Erro ao buscar pedido de venda por ID: {e}')
        return None


def search_sales_orders_by_name(
    models, db, uid, password, name, limit=100, offset=0
):
    try:
        domain = [
            '|',
            ['name', 'ilike', name],  # Case-insensitive contains
            ['partner_id.name', 'ilike', name],
        ]

        sales_orders = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'search_read',
            [domain],
            {'limit': limit, 'offset': offset, 'order': 'create_date desc'},
        )
        return sales_orders
    except Exception as e:
        print(f'Erro ao buscar pedidos de venda por nome: {e}')
        return []


def create_sales_order_in_odoo(order_data: dict, models, db, uid, password):
    try:
        # Prepara as linhas do pedido no formato esperado pelo Odoo
        order_lines = []
        for line in order_data.pop('order_line'):
            order_line = [0, 0, {
                'product_id': line['product_id'],
                'product_uom_qty': line['product_uom_qty'],
                'price_unit': line['price_unit']
            }]
            if line.get('name'):
                order_line[2]['name'] = line['name']
            order_lines.append(order_line)

        # Adiciona as linhas do pedido aos dados
        order_data['order_line'] = order_lines

        return models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'create',
            [order_data]
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar pedido de venda: {str(e)}'
        )


class SalesOrderService:
    @staticmethod
    def create_sales_order(order_data: Dict[str, Any]) -> int:
        """
        Cria um pedido de venda no Odoo.

        :param order_data: Dados do pedido de venda.
        :return: ID do pedido criado.
        """
        common, models = connect_to_odoo(ODOO_URL)
        uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

        if not uid:
            raise ValueError("Falha na autenticação no Odoo")

        try:
            # Preparar os dados para criação do pedido de venda
            order_lines = []
            for line in order_data["order_line"]:
                order_lines.append((0, 0, {
                    'product_id': line["product_id"],
                    'product_uom_qty': line["product_uom_qty"],
                    'price_unit': line["price_unit"],
                }))

            # Converter o campo date_order para string no formato esperado pelo Odoo
            date_order = order_data.get("date_order")
            if date_order and isinstance(date_order, datetime):
                date_order = date_order.strftime("%Y-%m-%d %H:%M:%S")

            # Preparar os valores para criação do pedido de venda
            order_vals = {
                'partner_id': order_data["partner_id"],
                'user_id': order_data["user_id"],
                'order_line': order_lines,
                'date_order': date_order,
                'client_order_ref': order_data.get("client_order_ref"),
                'type_name': order_data.get("type_name", "Pedido de venda")
            }

            # Adicionar opportunity_id se estiver presente
            if "opportunity_id" in order_data and order_data["opportunity_id"] is not None:
                order_vals["opportunity_id"] = order_data["opportunity_id"]

            # Criar o pedido de venda no Odoo
            order_id = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'sale.order',
                'create',
                [order_vals],
            )

            if not order_id:
                raise ValueError("Falha ao criar o pedido de venda")

            return order_id

        except Exception as e:
            raise ValueError(f"Erro ao criar o pedido de venda: {str(e)}")
