from datetime import datetime
from http import HTTPStatus
from typing import Any, Dict

from fastapi import HTTPException

from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
from app.services.authentication import authenticate_odoo, connect_to_odoo


def get_sales_orders(models, db, uid, password, limit=100, offset=0):
    """
    Obtém uma lista de pedidos de venda do Odoo.

    :param limit: Limite de registros a serem retornados
    :param offset: Deslocamento para paginação
    :return: Lista de pedidos ou lista vazia em caso de erro
    """
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
        print(f'Erro ao buscar as informações dos pedidos de venda: {e}')
        return []


def get_sales_order_by_id(models, db, uid, password, order_id):
    """
    Busca um pedido de venda específico pelo ID.

    :param order_id: ID do pedido a ser buscado
    :return: Dados do pedido ou None se não encontrado
    """
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
    """
    Busca pedidos de venda pelo nome ou nome do cliente.

    :param name: Termo de busca para o nome
    :param limit: Limite de registros a serem retornados
    :param offset: Deslocamento para paginação
    :return: Lista de pedidos encontrados ou lista vazia
    """
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
    """
    Cria um novo pedido de venda no Odoo.

    :param order_data: Dados do pedido de venda
    :return: ID do pedido criado ou exceção em caso de erro
    """
    try:
        # Prepara as linhas do pedido no formato esperado pelo Odoo
        order_lines = []
        for line in order_data.pop('order_line'):
            line_data = {
                'product_id': line['product_id'],
                'product_uom_qty': line['product_uom_qty'],
                'price_unit': line['price_unit'],
            }
            if line.get('name'):
                line_data['name'] = line['name']
            order_lines.append((0, 0, line_data))

        # Adiciona as linhas do pedido aos dados
        order_data['order_line'] = order_lines

        return models.execute_kw(
            db, uid, password, 'sale.order', 'create', [order_data]
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao criar pedido de venda: {str(e)}',
        )


class SalesOrderService:
    """
    Serviço para manipulação de pedidos de venda no Odoo.
    Contém métodos para criar, buscar e atualizar pedidos.
    """

    @staticmethod
    def create_sales_order(order_data: Dict[str, Any]) -> int:
        """
        Cria um pedido de venda no Odoo e vincula a uma oportunidade se fornecido.

        :param order_data: Dados do pedido de venda
        :return: ID do pedido criado
        :raises ValueError: Se falhar a autenticação, validação ou criação
        """
        common, models = connect_to_odoo(ODOO_URL)
        uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

        if not uid:
            raise ValueError('Falha na autenticação no Odoo')

        try:
            # Prepara as linhas do pedido
            order_lines = []

            # Se não houver linhas de pedido, adiciona uma linha com valores default
            if not order_data.get('order_line'):
                default_line = {
                    'product_id': 119,
                    'product_uom_qty': 1,
                    'price_unit': 1,
                }
                order_lines.append((0, 0, default_line))
            else:
                for line in order_data.get('order_line', []):
                    line_data = {
                        'product_id': line.get('product_id', 119),
                        'product_uom_qty': line.get('product_uom_qty', 1),
                        'price_unit': line.get('price_unit', 1),
                    }
                    # Adiciona descrição se disponível
                    if 'name' in line:
                        line_data['name'] = line['name']

                    order_lines.append((0, 0, line_data))

            # Dados obrigatórios para o pedido
            order_vals = {
                'partner_id': order_data.get('partner_id'),
                'order_line': order_lines,
                'user_id': order_data.get('user_id', 3),  # Default user_id = 3
            }

            # Formata data do pedido para o formato esperado pelo Odoo
            date_order = order_data.get('date_order')
            if date_order:
                if isinstance(date_order, datetime):
                    date_order = date_order.strftime('%Y-%m-%d %H:%M:%S')
                order_vals['date_order'] = date_order
            else:
                # Se não foi fornecida uma data, usa a data atual
                order_vals['date_order'] = datetime.now().strftime(
                    '%Y-%m-%d %H:%M:%S'
                )

            # Adiciona referência do cliente se fornecida
            if 'client_order_ref' in order_data:
                order_vals['client_order_ref'] = order_data['client_order_ref']

            # Adiciona o tipo do pedido (com valor default se não fornecido)
            order_vals['type_name'] = order_data.get(
                'type_name', 'Pedido de venda'
            )

            # Verifica e vincula oportunidade se fornecida
            if (
                'opportunity_id' in order_data
                and order_data['opportunity_id'] is not None
            ):
                # Verifica se a oportunidade existe
                opportunity_exists = models.execute_kw(
                    ODOO_DB,
                    uid,
                    ODOO_PASSWORD,
                    'crm.lead',
                    'search_count',
                    [[['id', '=', order_data['opportunity_id']]]],
                )

                if opportunity_exists:
                    order_vals['opportunity_id'] = order_data['opportunity_id']
                else:
                    raise ValueError(
                        f'Oportunidade com ID {order_data["opportunity_id"]} não existe'
                    )

            # Cria o pedido de venda no Odoo
            order_id = models.execute_kw(
                ODOO_DB,
                uid,
                ODOO_PASSWORD,
                'sale.order',
                'create',
                [order_vals],
            )

            if not order_id:
                raise ValueError('Falha ao criar o pedido de venda')

            return order_id

        except Exception as e:
            raise ValueError(f'Erro ao criar o pedido de venda: {str(e)}')


def update_sales_order_fields(
    models, db, uid, password, order_id, fields_data
):
    """
    Atualiza campos específicos de um pedido de venda.
    :param order_id: ID do pedido a ser atualizado
    :param fields_data: Dicionário com os campos a serem atualizados
    :return: True se bem-sucedido, None se falhar
    """
    try:
        success = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'write',
            [[order_id], fields_data],
        )
        return success
    except Exception as e:
        print(f'Erro ao atualizar campos do pedido de venda: {e}')
        return None
