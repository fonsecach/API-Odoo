from pydantic import BaseModel, EmailStr, constr

class Company_default(BaseModel):
    company_type: int = 0
    name: str
    vat: str
    country_id: int = 31
    phone: str
    email: EmailStr


class Company_return(Company_default):
    company_id: int


class Message(BaseModel):
    message: str
