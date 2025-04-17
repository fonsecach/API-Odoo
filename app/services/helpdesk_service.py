def get_helpdesk_info(models, db, uid, password, limit=100, offset=0):
    try:
        helpdesk_info = models.execute_kw(
            db,
            uid,
            password,
            'helpdesk.ticket',
            'search_read',
            [[]],
            {'limit': limit, 'offset': offset},
        )
        return helpdesk_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações dos tickets: {e}')
        return []


def get_helpdesk_info_by_team_id(
    models, db, uid, password, team_id, limit=100, offset=0
):
    try:
        helpdesk_info = models.execute_kw(
            db,
            uid,
            password,
            'helpdesk.ticket',
            'search_read',
            [[['team_id', '=', team_id]]],
            {'limit': limit, 'offset': offset},
        )
        return helpdesk_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações dos tickets: {e}')
        return []


def get_helpdesk_info_by_team_and_id(
    models, db, uid, password, team_id, stage_id, limit=100, offset=0
):
    try:
        helpdesk_info = models.execute_kw(
            db,
            uid,
            password,
            'helpdesk.ticket',
            'search_read',
            [[['stage_id', '=', stage_id], ['team_id', '=', team_id]]],
            {
                'limit': limit,
                'offset': offset,
            },
        )
        return helpdesk_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações dos tickets: {e}')
        return []
