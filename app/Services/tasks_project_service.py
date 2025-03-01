# app/Services/tasks_project_service.py

def get_tasks_info(models, db, uid, password, limit=100, offset=0):
    """
    Obtém informações de várias tarefas.
    :param limit: Limite de registros a serem retornados
    :param offset: Deslocamento para paginação
    :return: Lista de tarefas ou lista vazia em caso de erro
    """
    try:
        tasks_info = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[]],
            {
                'limit': limit,
                'offset': offset,
                'fields': ['id', 'name', 'project_id', 'stage_id', 'sale_order_id'],
            },
        )
        return tasks_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das tarefas: {e}')
        return []


def get_task_by_id(models, db, uid, password, task_id):
    """
    Obtém uma tarefa pelo seu ID.
    :param task_id: ID da tarefa a ser recuperada
    :return: Informações da tarefa ou None se não for encontrada
    """
    try:
        task_info = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[['id', '=', task_id]]],
            {'fields': ['id', 'name', 'project_id', 'stage_id', 'sale_order_id']},
        )
        return task_info[0] if task_info else None
    except Exception as e:
        print(f'Erro ao recuperar tarefa por ID: {e}')
        return None


def get_task_by_project_and_id(models, db, uid, password, project_id, task_id):
    """
    Obtém uma tarefa específica de um projeto.
    :param project_id: ID do projeto
    :param task_id: ID da tarefa
    :return: Informações da tarefa ou None se não for encontrada
    """
    try:
        task_info = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[['id', '=', task_id], ['project_id', '=', project_id]]],
            {'fields': ['id', 'name', 'project_id', 'stage_id', 'sale_order_id']},
        )
        return task_info[0] if task_info else None
    except Exception as e:
        print(f'Erro ao buscar e ler informações da tarefa: {e}')
        return None


def create_task(models, db, uid, password, task_data):
    """
    Cria uma nova tarefa no Odoo.
    :param task_data: Dicionário com os dados da tarefa
    :return: ID da tarefa criada ou None em caso de erro
    """
    try:
        task_id = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'create',
            [task_data],
        )
        return task_id
    except Exception as e:
        print(f'Erro ao criar tarefa: {e}')
        return None


def update_task_fields(models, db, uid, password, task_id, fields_data):
    """
    Atualiza campos específicos de uma tarefa.
    :param task_id: ID da tarefa a ser atualizada
    :param fields_data: Dicionário com os campos a serem atualizados
    :return: True se bem-sucedido, None se falhar
    """
    try:
        success = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'write',
            [[task_id], fields_data],
        )
        return success
    except Exception as e:
        print(f'Erro ao atualizar campos da tarefa: {e}')
        return None


def update_task_sale_order(models, db, uid, password, task_id, sale_order_id):
    """
    Atualiza uma tarefa com o ID de um pedido de venda.
    :param task_id: ID da tarefa a ser atualizada
    :param sale_order_id: ID do pedido de venda a ser vinculado
    :return: True se bem-sucedido, None se falhar
    """
    try:
        success = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'write',
            [[task_id], {'sale_order_id': sale_order_id}],
        )
        return success
    except Exception as e:
        print(f'Erro ao atualizar tarefa com ID do pedido de venda: {e}')
        return None


def create_task_attachment(models, db, uid, password, task_id, file_name, file_content):
    """
    Adiciona um anexo a uma tarefa.
    :param task_id: ID da tarefa
    :param file_name: Nome do arquivo
    :param file_content: Conteúdo do arquivo codificado em base64
    :return: ID do anexo criado ou None em caso de erro
    """
    try:
        attachment_data = {
            "name": file_name,
            "datas": file_content,
            "res_model": "project.task",
            "res_id": task_id,
        }

        attachment_id = models.execute_kw(
            db,
            uid,
            password,
            "ir.attachment",
            "create",
            [attachment_data],
        )
        return attachment_id
    except Exception as e:
        print(f'Erro ao anexar arquivo à tarefa: {e}')
        return None
