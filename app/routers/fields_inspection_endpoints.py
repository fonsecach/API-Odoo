# from http import HTTPStatus
# from typing import Dict, List, Optional

# from fastapi import APIRouter, HTTPException, Query

# from app.config.settings import ODOO_DB, ODOO_PASSWORD, ODOO_URL, ODOO_USERNAME
# from app.services.authentication import authenticate_odoo, connect_to_odoo
# from app.services.fields_inspection_service import (
#     get_available_models,
#     get_model_fields,
# )

# router = APIRouter(prefix='/fields', tags=['Fields Inspection'])


# @router.get(
#     '/models',
#     summary='List available models',
#     description='Get a list of all available models in Odoo, with optional filtering by name.',
# )
# async def list_available_models(
#     search: Optional[str] = Query(
#         default=None,
#         description='Optional search term to filter models by name or technical name',
#     ),
# ):
#     """
#     List available models in Odoo, with optional filtering.

#     Args:
#         search: Optional search term to filter models by name or technical name

#     Returns:
#         A list of available models with basic information
#     """
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Failed to authenticate with Odoo',
#         )

#     model_records = get_available_models(
#         models, ODOO_DB, uid, ODOO_PASSWORD, search
#     )

#     return {'count': len(model_records), 'models': model_records}


# @router.get(
#     '/{model_name}',
#     summary='Inspect model fields',
#     description='Retrieve field information for a specified Odoo model with various filtering options.',
# )
# async def inspect_model_fields(
#     model_name: str,
#     attributes: Optional[List[str]] = Query(
#         default=None,
#         description="Specific field attributes to return. Defaults to ['string', 'help', 'type']",
#     ),
#     fields: Optional[List[str]] = Query(
#         default=None,
#         description='Filter to return only specific fields by name',
#     ),
#     field_type: Optional[str] = Query(
#         default=None,
#         description="Filter to return only fields of a specific type (e.g., 'many2one', 'char', etc.)",
#     ),
#     search: Optional[str] = Query(
#         default=None,
#         description='Search term to filter fields by name or label',
#     ),
# ):
#     """
#     Inspect fields of an Odoo model with advanced filtering options.

#     Args:
#         model_name: The technical name of the model (e.g., 'res.partner', 'crm.lead')
#         attributes: Optional list of field attributes to return
#         fields: Optional list of specific field names to return
#         field_type: Optional filter to return only fields of a specific type
#         search: Optional search term to filter fields by name or label

#     Returns:
#         A dictionary containing filtered information about the model's fields
#     """
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Failed to authenticate with Odoo',
#         )

#     fields_info = get_model_fields(
#         models,
#         ODOO_DB,
#         uid,
#         ODOO_PASSWORD,
#         model_name,
#         attributes,
#         fields,
#         field_type,
#         search,
#     )

#     return {
#         'model': model_name,
#         'fields_count': len(fields_info),
#         'fields': fields_info,
#     }


# @router.get(
#     '/{model_name}/field_types',
#     summary='Get field types for a model',
#     description='Retrieve a list of all field types used in a specific model.',
# )
# async def get_model_field_types(model_name: str):
#     """
#     Get a list of all field types used in a specific model.

#     Args:
#         model_name: The technical name of the model (e.g., 'res.partner', 'crm.lead')

#     Returns:
#         A dictionary with field types as keys and counts as values
#     """
#     common, models = connect_to_odoo(ODOO_URL)
#     uid = authenticate_odoo(common, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

#     if not uid:
#         raise HTTPException(
#             status_code=HTTPStatus.UNAUTHORIZED,
#             detail='Failed to authenticate with Odoo',
#         )

#     fields_info = get_model_fields(
#         models, ODOO_DB, uid, ODOO_PASSWORD, model_name, ['type']
#     )

#     # Collect field types
#     field_types: Dict[str, int] = {}
#     for field_data in fields_info.values():
#         field_type = field_data.get('type', 'unknown')
#         field_types[field_type] = field_types.get(field_type, 0) + 1

#     return {'model': model_name, 'field_types': field_types}
