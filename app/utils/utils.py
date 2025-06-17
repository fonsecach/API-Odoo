def clean_vat(vat: str) -> str:
    """
    Limpa um CPF ou CNPJ, removendo caracteres não numéricos.
    Levanta um ValueError se o resultado não tiver 11 (CPF) ou 14 (CNPJ) dígitos.
    """
    if not isinstance(vat, str):
        raise ValueError('A entrada deve ser uma string.')

    cleaned_vat = ''.join(filter(str.isdigit, vat))

    # Aceita comprimentos de 11 (CPF) e 14 (CNPJ)
    if len(cleaned_vat) not in [11, 14]:
        raise ValueError('CPF/CNPJ inválido. Deve conter 11 ou 14 dígitos.')

    return cleaned_vat