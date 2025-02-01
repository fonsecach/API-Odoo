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

    
