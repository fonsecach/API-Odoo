from http import HTTPStatus
from typing import Dict, List

from fastapi import HTTPException

from app.schemas.schemas import SelectionFieldValue


def update_selection_field_values(
    models,
    db: str,
    uid: int,
    password: str,
    model_name: str,
    field_name: str,
    values: List[SelectionFieldValue],
) -> Dict:
    """
    Atualiza um campo de seleção personalizado adicionando novos valores aos existentes.
    """
    try:
        # Verifica se o modelo existe
        model_exists = models.execute_kw(
            db,
            uid,
            password,
            'ir.model',
            'search_count',
            [[['model', '=', model_name]]],
        )

        if not model_exists:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Modelo '{model_name}' não encontrado no Odoo",
            )

        # Obtém o registro ir.model.fields do campo
        field_ids = models.execute_kw(
            db,
            uid,
            password,
            'ir.model.fields',
            'search_read',
            [[['model', '=', model_name], ['name', '=', field_name]]],
            {'fields': ['id', 'selection', 'ttype']},
        )

        if not field_ids:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Definição do campo '{field_name}' não encontrada no modelo '{model_name}'",
            )

        field_id = field_ids[0]['id']
        field_type = field_ids[0].get('ttype')

        # Verifica se é um campo de seleção
        if field_type != 'selection':
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=f"Campo '{field_name}' não é um campo de seleção. Tipo atual: {field_type}",
            )

        current_selection_str = field_ids[0].get('selection', '[]')

        # Converte a string de seleção atual para obter os valores existentes
        try:
            import ast

            current_selection = ast.literal_eval(current_selection_str)
        except (SyntaxError, ValueError):
            current_selection = []

        # Converte a seleção atual para um dicionário para facilitar a manipulação
        current_selection_dict = {val: name for val, name in current_selection}

        # Adiciona novos valores aos existentes (atualizando rótulos se o valor já existir)
        new_values_added = False
        for new_value in values:
            if new_value.value not in current_selection_dict:
                new_values_added = True
            current_selection_dict[new_value.value] = new_value.name

        # Se nenhum valor novo foi adicionado, retorna os valores atuais
        if not new_values_added:
            return {
                'message': 'Nenhum valor novo adicionado, todos os valores já existem',
                'model': model_name,
                'field': field_name,
                'current_values': [
                    {'value': val, 'name': name}
                    for val, name in current_selection_dict.items()
                ],
            }

        # Converte de volta para o formato de seleção esperado pelo Odoo
        updated_selection = [
            (val, name) for val, name in current_selection_dict.items()
        ]

        # Atualiza os valores do campo de seleção
        # Aqui usamos o parâmetro 'selection_ids' para garantir que o Odoo processe corretamente
        selection_ids = [
            (0, 0, {'value': val, 'name': name})
            for val, name in current_selection_dict.items()
        ]

        try:
            # Primeiro, atualiza a definição do campo com a seleção completa
            result = models.execute_kw(
                db,
                uid,
                password,
                'ir.model.fields',
                'write',
                [field_id, {'selection': str(updated_selection)}],
            )

            # Tenta uma abordagem alternativa usando o ir.model.data para forçar uma atualização
            try:
                models.execute_kw(
                    db, uid, password, 'ir.model.data', 'clear_caches', []
                )
            except Exception as cache_error:
                print(
                    f'Aviso: Não foi possível limpar o cache do ir.model.data: {str(cache_error)}'
                )

            # Tenta atualizar o campo no registry para forçar atualização
            try:
                registry_update = models.execute_kw(
                    db,
                    uid,
                    password,
                    'ir.model',
                    'write',
                    [
                        [
                            models.execute_kw(
                                db,
                                uid,
                                password,
                                'ir.model',
                                'search',
                                [[['model', '=', model_name]]],
                            )[0]
                        ],
                        {'name': model_name},
                    ],
                )
            except Exception as reg_error:
                print(
                    f'Aviso: Não foi possível atualizar o registry: {str(reg_error)}'
                )

        except Exception as e:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f'Falha ao atualizar valores do campo de seleção: {str(e)}',
            )

        return {
            'message': f'Valores de seleção para {field_name} atualizados com sucesso',
            'model': model_name,
            'field': field_name,
            'new_values_added': [
                v.value for v in values if v.value in current_selection_dict
            ],
            'current_values': [
                {'value': val, 'name': name}
                for val, name in sorted(
                    current_selection_dict.items(), key=lambda x: x[0]
                )
            ],
        }

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f'Erro ao atualizar campo de seleção: {str(e)}',
        )
