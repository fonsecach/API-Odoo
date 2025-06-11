# from http import HTTPStatus

# from fastapi import APIRouter, HTTPException

# from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
# from app.schemas.schemas import SelectionFieldUpdate
# from app.services.authentication import authenticate_odoo, connect_to_odoo
# from app.services.custom_fields_service import update_selection_field_values

# router = APIRouter(prefix='/custom-fields', tags=['Custom Fields'])


# @router.put(
#     '/selection',
#     summary='Atualiza valores de campo de seleção',
#     response_description='Valores atualizados com sucesso',
# )
# async def update_selection_field(update_data: SelectionFieldUpdate):
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Falha na autentificação no Odoo',
#         )

#     result = update_selection_field_values(
#         models,
#         ODOO_DB,
#         uid,
#         ODOO_PASSWORD,
#         update_data.model_name,
#         update_data.field_name,
#         update_data.values,
#     )

#     return result
