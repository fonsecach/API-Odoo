def get_companies_info(models, db, uid, password, limit=5):
    """Busca e retorna informações detalhadas das empresas cadastradas, limitado pelo parâmetro limit."""
    fields_to_read = ['name', 'country_id', 'comment', 'email', 'phone', 'vat']
    domain = [['is_company', '=', True]]

    try:
        # Buscar e ler informações das empresas
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


def display_company_info(companies_info):
    """Exibe as informações detalhadas de cada empresa de forma organizada."""
    for company in companies_info:
        name = company.get('name', 'N/A')

        country = company.get('country_id')
        country_name = country[1] if isinstance(country, list) and len(country) > 1 else 'País não informado'

        comment = company.get('comment', 'Sem comentários')
        email = company.get('email', 'Sem e-mail')
        phone = company.get('phone', 'Sem telefone')
        vat = company.get('vat', 'CNPJ não informado')

        print(f'\nEmpresa: {name}')
        print(f'CNPJ: {vat}')
        print(f'País: {country_name}')
        print(f'Comentário: {comment}')
        print(f'E-mail: {email}')
        print(f'Telefone: {phone}')
