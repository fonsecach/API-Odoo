
def get_opportunities_info(models, db, uid, password, limit=100, offset=0):
    try:
        opportunities_info = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'search_read',
            [[]],
            {
                'limit': limit,
                'offset': offset
            }
        )
        return opportunities_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das oportunidades: {e}')
        return []


def get_opportunity_by_id(models, db, uid, password, opportunity_id):
    try:
        opportunities_info = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'read',
            [opportunity_id]
        )
        return opportunities_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações da oportunidade: {e}')
        return []

def create_opportunity_in_crm(opportunity_info, models, db, uid, password):
    try:
        opportunity_id = models.execute_kw(
            db,
            uid,
            password,
            'crm.lead',
            'create',
            [opportunity_info]
        )
        return opportunity_id
    except Exception as e:
        print(f'Erro ao criar oportunidade: {e}')
        return None
