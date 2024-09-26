def clean_vat(vat: str) -> str:
    cleaned_vat = ''.join(filter(str.isdigit, vat))

    if len(cleaned_vat) != 14:
        raise ValueError("CNPJ inválido. Deve conter exatamente 14 dígitos numéricos.")

    return cleaned_vat
