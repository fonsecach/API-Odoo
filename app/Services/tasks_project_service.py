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


def get_tasks_by_stage_name(models, db, uid, password, project_id, stage_name, limit=100, offset=0):
    """
    Obtém tarefas de um projeto filtradas pelo nome do estágio.
    :param project_id: ID do projeto
    :param stage_name: Nome do estágio para filtrar
    :param limit: Limite de registros a serem retornados
    :param offset: Deslocamento para paginação
    :return: Lista de tarefas ou lista vazia em caso de erro
    """
    try:
        # Primeiro, busca o ID do estágio pelo nome
        stage_ids = models.execute_kw(
            db,
            uid,
            password,
            'project.task.type',
            'search',
            [[['name', 'ilike', stage_name]]],
        )
        
        if not stage_ids:
            print(f'Nenhum estágio encontrado com nome {stage_name}')
            return []
        
        # Busca tarefas com o project_id e stage_id correspondentes
        tasks_info = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[['project_id', '=', project_id], ['stage_id', 'in', stage_ids]]],
            {
                'limit': limit,
                'offset': offset,
                'fields': ['id', 'name', 'project_id', 'stage_id', 'sale_order_id', 
                           'x_studio_tese_2', 'x_studio_segmento', 'partner_id'],
            },
        )
        
        return tasks_info
    except Exception as e:
        print(f'Erro ao buscar tarefas por estágio: {e}')
        return []


def update_task_stage(models, db, uid, password, task_id, stage_id):
    """
    Atualiza o estágio de uma tarefa.
    :param task_id: ID da tarefa a ser atualizada
    :param stage_id: ID do estágio para o qual a tarefa deve ser movida
    :return: True se bem-sucedido, None se falhar
    """
    try:
        success = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'write',
            [[task_id], {'stage_id': stage_id}],
        )
        return success
    except Exception as e:
        print(f'Erro ao atualizar estágio da tarefa: {e}')
        return None
    

def transfer_task_messages(models, db, uid, password, source_task_id, target_task_id):
    """
    Transfere as mensagens (message_ids) de uma tarefa para outra, preservando as mensagens existentes
    na tarefa de destino.
    
    :param source_task_id: ID da tarefa de origem das mensagens
    :param target_task_id: ID da tarefa de destino para onde as mensagens serão copiadas
    :return: True se a operação for bem-sucedida, None em caso de erro
    """
    try:
        # Verificar se ambas as tarefas existem
        tasks = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[['id', 'in', [source_task_id, target_task_id]]]],
            {'fields': ['id', 'name', 'message_ids']}
        )

        if len(tasks) != 2:
            print(f'Uma ou ambas as tarefas não foram encontradas: origem={source_task_id}, destino={target_task_id}')
            return None

        # Identificar qual é a tarefa de origem e qual é a de destino
        source_task = next((task for task in tasks if task['id'] == source_task_id), None)
        target_task = next((task for task in tasks if task['id'] == target_task_id), None)

        if not source_task or not target_task:
            print(f'Não foi possível identificar as tarefas corretamente')
            return None

        # Obter as mensagens da tarefa de origem
        source_messages = source_task.get('message_ids', [])
        
        if not source_messages:
            print(f'A tarefa de origem não possui mensagens para transferir')
            return True  # Retorna True pois não há erro, apenas não há mensagens
        
        # Verificar se a tarefa de destino já tem mensagens
        target_messages = target_task.get('message_ids', [])
        
        # Criar cópias das mensagens da tarefa de origem para a tarefa de destino
        for message_id in source_messages:
            # Verificar se a mensagem já existe na tarefa de destino
            if message_id in target_messages:
                continue
                
            # Obter detalhes da mensagem original
            message_data = models.execute_kw(
                db,
                uid,
                password,
                'mail.message',
                'read',
                [message_id],
                {'fields': ['body', 'subject', 'message_type', 'subtype_id', 'author_id']}
            )
            
            if not message_data:
                continue
                
            message_data = message_data[0]
            
            # Criar uma nova mensagem na tarefa de destino
            new_message = {
                'body': message_data['body'],
                'subject': message_data.get('subject', ''),
                'message_type': message_data['message_type'],
                'subtype_id': message_data.get('subtype_id', False) and message_data['subtype_id'][0],
                'author_id': message_data.get('author_id', False) and message_data['author_id'][0],
                'model': 'project.task',
                'res_id': target_task_id,
            }
            
            models.execute_kw(
                db,
                uid,
                password,
                'mail.message',
                'create',
                [new_message]
            )
        
        print(f'Mensagens transferidas com sucesso da tarefa {source_task_id} para a tarefa {target_task_id}')
        return True
        
    except Exception as e:
        print(f'Erro ao transferir mensagens entre tarefas: {e}')
        return None


# Alternativa: função que utiliza a API interna do Odoo
# Esta abordagem pode ser mais eficiente, mas depende de como o Odoo está configurado
def transfer_task_messages_v2(models, db, uid, password, source_task_id, target_task_id):
    """
    Transfere as mensagens (message_ids) de uma tarefa para outra usando as funções nativas do Odoo.
    Esta versão utiliza a API de mensagens do Odoo, que pode ser mais eficiente.
    
    :param source_task_id: ID da tarefa de origem das mensagens
    :param target_task_id: ID da tarefa de destino para onde as mensagens serão copiadas
    :return: True se a operação for bem-sucedida, None em caso de erro
    """
    try:
        # Verificar se ambas as tarefas existem
        source_task_exists = models.execute_kw(
            db, uid, password, 'project.task', 'search_count', [[['id', '=', source_task_id]]]
        )
        
        target_task_exists = models.execute_kw(
            db, uid, password, 'project.task', 'search_count', [[['id', '=', target_task_id]]]
        )
        
        if not source_task_exists or not target_task_exists:
            print(f'Uma ou ambas as tarefas não foram encontradas: origem={source_task_id}, destino={target_task_id}')
            return None
            
        # Obter as mensagens da tarefa de origem
        source_messages = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'read',
            [source_task_id],
            {'fields': ['message_ids']}
        )[0]['message_ids']
        
        if not source_messages:
            print(f'A tarefa de origem não possui mensagens para transferir')
            return True
            
        # Utilizar método message_post para criar cópias das mensagens
        for message_id in source_messages:
            message_data = models.execute_kw(
                db,
                uid,
                password,
                'mail.message',
                'read',
                [message_id],
                {'fields': ['body', 'subject']}
            )[0]
            
            # Adicionar a mensagem à tarefa de destino
            models.execute_kw(
                db,
                uid,
                password,
                'project.task',
                'message_post',
                [target_task_id],
                {
                    'body': message_data['body'],
                    'subject': message_data.get('subject', 'Mensagem transferida'),
                    'message_type': 'comment',
                }
            )
            
        print(f'Mensagens transferidas com sucesso da tarefa {source_task_id} para a tarefa {target_task_id}')
        return True
        
    except Exception as e:
        print(f'Erro ao transferir mensagens entre tarefas: {e}')
        return None
