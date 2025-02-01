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
            {'limit': 1}
        )
        return sales_order[0] if sales_order else None
    except Exception as e:
        print(f'Erro ao buscar pedido de venda por ID: {e}')
        return None

def search_sales_orders_by_name(models, db, uid, password, name, limit=100, offset=0):
    try:
        domain = [
            '|',
            ['name', 'ilike', name],  # Case-insensitive contains
            ['partner_id.name', 'ilike', name]  
        ]
        
        sales_orders = models.execute_kw(
            db,
            uid,
            password,
            'sale.order',
            'search_read',
            [domain],
            {
                'limit': limit,
                'offset': offset,
                'order': 'create_date desc' 
            }
        )
        return sales_orders
    except Exception as e:
        print(f'Erro ao buscar pedidos de venda por nome: {e}')
        return []
    
