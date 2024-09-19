

def get_oportunities_info(models, db, uid, password, limit=100):

    try:
        oportunities_info = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'search_read',
            [[]],
            {
                'limit': limit
            }
        )
        return oportunities_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das oportunidades: {e}')
        return []
