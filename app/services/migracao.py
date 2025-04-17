from typing import Dict


def get_partners_by_names(
    names: list[str], models, db: str, uid: int, password: str
) -> Dict[str, int]:
    try:
        domain = ['|'] * (len(names) - 1) + [
            ('name', 'ilike', name) for name in names
        ]

        partners = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
            {'fields': ['id', 'name']},
        )

        return {partner['name']: partner['id'] for partner in partners}

    except Exception as e:
        print(f'Erro ao buscar empresas: {e}')
        return None
