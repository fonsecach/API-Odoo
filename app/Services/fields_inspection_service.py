from http import HTTPStatus
from typing import Any, Dict, List, Optional

from fastapi import HTTPException


def get_model_fields(
    models, db: str, uid: int, password: str, model_name: str,
    attributes: Optional[List[str]] = None,
    field_names: Optional[List[str]] = None,
    field_type: Optional[str] = None,
    search_term: Optional[str] = None
) -> Dict:
    """
    Get fields information for a specific Odoo model with filtering options.
    
    Args:
        models: The XML-RPC model proxy object
        db: The Odoo database name
        uid: The authenticated user ID
        password: The user password
        model_name: The name of the model to inspect
        attributes: Optional list of field attributes to return (default: ['string', 'help', 'type'])
        field_names: Optional list of specific field names to return
        field_type: Optional filter to return only fields of a specific type (e.g., 'many2one', 'char', etc.)
        search_term: Optional search term to filter fields by name or label
        
    Returns:
        A dictionary containing filtered field information for the specified model
    """
    try:
        # Default attributes that are most useful for inspection
        if attributes is None:
            attributes = ['string', 'help', 'type']

        # Get all fields first
        fields_info = models.execute_kw(
            db,
            uid,
            password,
            model_name,
            'fields_get',
            [],
            {'attributes': attributes}
        )

        # Apply filters
        filtered_fields = {}

        for field_name, field_data in fields_info.items():
            # Filter by specific field names if provided
            if field_names and field_name not in field_names:
                continue

            # Filter by field type if provided
            if field_type and field_data.get('type') != field_type:
                continue

            # Filter by search term (in field name or label)
            if search_term:
                search_term_lower = search_term.lower()
                field_label = field_data.get('string', '').lower()
                if (search_term_lower not in field_name.lower() and
                    search_term_lower not in field_label):
                    continue

            # If it passes all filters, add it to the result
            filtered_fields[field_name] = field_data

        return filtered_fields

    except Exception as e:
        # Check if exception is due to model not existing
        if "Object does not exist" in str(e):
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail=f"Model '{model_name}' does not exist in Odoo."
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                detail=f"Error fetching fields for model '{model_name}': {str(e)}"
            )


def get_available_models(models, db: str, uid: int, password: str, search_term: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a list of available models in Odoo, with optional filtering by name.
    
    Args:
        models: The XML-RPC model proxy object
        db: The Odoo database name
        uid: The authenticated user ID
        password: The user password
        search_term: Optional search term to filter models
        
    Returns:
        A list of dictionaries with model information
    """
    try:
        # Find all models by searching for ir.model records
        domain = []
        if search_term:
            domain = [
                '|',
                ('model', 'ilike', search_term),
                ('name', 'ilike', search_term)
            ]

        model_records = models.execute_kw(
            db,
            uid,
            password,
            'ir.model',
            'search_read',
            [domain],
            {'fields': ['model', 'name', 'info', 'state']}
        )

        return model_records

    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            detail=f"Error fetching available models: {str(e)}"
        )
