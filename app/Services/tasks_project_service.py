def get_tasks_info(models, db, uid, password, limit=100, offset=0):
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
                'fields': ['id', 'name', 'project_id', 'stage_id'],
            },
        )
        return tasks_info
    except Exception as e:
        print(f'Erro ao buscar e ler informações das tarefas: {e}')
        return []


def get_task_by_project_and_id(models, db, uid, password, project_id, task_id):
    try:
        task_info = models.execute_kw(
            db,
            uid,
            password,
            'project.task',
            'search_read',
            [[['id', '=', task_id], ['project_id', '=', project_id]]],
            {'fields': ['id', 'name', 'project_id', 'stage_id']},
        )
        return task_info if task_info else None
    except Exception as e:
        print(f'Erro ao buscar e ler informações da tarefa: {e}')
        return None
