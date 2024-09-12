def get_companies_info(models, db, uid, password, limit=100):
    """Busca e retorna informações detalhadas das empresas cadastradas, limitado pelo parâmetro limit."""
    fields_to_read = ['name', 'country_id', 'comment', 'email', 'phone', 'vat']
    domain = [['is_company', '=', True]]

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
            {
                'fields': fields_to_read,
                'limit': limit
            }
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das empresas: {e}')
        return []

def get_company_by_vat(vat, models, db, uid, password):
    fields_to_read = ['name', 'country_id', 'email', 'phone', 'vat']
    domain = [['vat', '=', vat]]  # Usar o vat dinâmico

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
            {'fields': fields_to_read}
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar empresa pelo VAT {vat}: {e}')
        return []

def get_company_by_id(id, models, db, uid, password):
    fields_to_read = ['name', 'country_id', 'email', 'phone', 'vat']
    domain = [['id', '=', id]]

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
            {'fields': fields_to_read}
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar empresa pelo ID {id}: {e}')
        return []

def create_company_in_odoo(company_info, models, db, uid, password):
    try:
        company_id = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'create',
            [company_info]
        )
        return company_id
    except Exception as e:
        print(f'Erro ao criar empresa: {e}')
        return None
