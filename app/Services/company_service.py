from http import HTTPStatus
from fastapi import HTTPException


def get_clients_info(models, db, uid, password, limit=100, offset=0):
    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [[]],
            {'limit': limit, 'offset': offset},
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das empresas: {e}')
        return []


def get_company_by_vat(vat, models, db, uid, password):
    domain = [['vat', '=', vat]]

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar empresa pelo VAT {vat}: {e}')
        return []


def fetch_client_by_complete_name(name, models, db, uid, password):
    domain = [['complete_name', '=', name]]

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar cliente pelo nome {name}: {e}')
        return []


def get_company_by_id(id, models, db, uid, password):
    domain = [['id', '=', id]]

    try:
        companies_info = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'search_read',
            [domain],
        )
        return companies_info
    except Exception as e:
        print(f'Erro ao buscar empresa pelo ID {id}: {e}')
        return []


def create_company_in_odoo(company_info, models, db, uid, password):
    try:
        company_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create', [company_info]
        )
        return company_id
    except Exception as e:
        print(f'Erro ao criar empresa: {e}')
        return None


def update_company_in_odoo(
    company_id, company_info, models, db, uid, password
):
    try:
        success = models.execute_kw(
            db,
            uid,
            password,
            'res.partner',
            'write',
            [[company_id], company_info],
        )
        return success
    except Exception as e:
        print(f'Erro ao atualizar empresa: {e}')
        return None


def delete_company_in_odoo(company_id, models, db, uid, password):
    try:
        company_id = models.execute_kw(
            db, uid, password, 'res.partner', 'unlink', [company_id]
        )
        return company_id
    except Exception as e:
        print(f'Erro ao excluir empresa: {e}')
        return None


def get_or_create_partner(contact_name, models, db, uid, password):
    """Verifica se o cliente já existe, senão cria um novo."""
    try:
        # 🔹 Tenta encontrar o cliente pelo nome
        existing_partners = models.execute_kw(
            db, uid, password, 'res.partner', 'search_read',
            [[['name', '=', contact_name]]], {'fields': ['id']}
        )

        if existing_partners:
            return existing_partners[0]['id']  # Retorna o ID se já existir

        # 🔹 Se não existir, cria um novo cliente
        partner_id = models.execute_kw(
            db, uid, password, 'res.partner', 'create',
            [{'name': contact_name}]
        )

        return partner_id
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao buscar/criar cliente: {str(e)}',
        )