import xmlrpc.client


def connect_to_odoo(url):
    """Cria e retorna o proxy para comunicação com o servidor Odoo via XML-RPC."""
    return xmlrpc.client.ServerProxy(
        f'{url}/xmlrpc/2/common'
    ), xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')


def authenticate_odoo(common, db, username, password):
    """Autentica o usuário no Odoo e retorna o UID ou None se falhar."""
    try:
        uid = common.authenticate(db, username, password, {})
        if uid:
            print(f'Autenticação bem-sucedida. UID: {uid}')
        else:
            print('Falha na autenticação.')
        return uid
    except Exception as e:
        print(f'Erro ao autenticar: {e}')
        return None
