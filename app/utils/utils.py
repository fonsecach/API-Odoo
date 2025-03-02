def clean_vat(vat: str) -> str:
    cleaned_vat = ''.join(filter(str.isdigit, vat))
    
    len_vat = 14

    if len(cleaned_vat) != len_vat:
        raise ValueError(
            'CNPJ inválido. Deve conter exatamente 14 dígitos.'
        )

    return cleaned_vat
