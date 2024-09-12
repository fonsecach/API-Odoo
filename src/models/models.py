from pydantic import BaseModel, EmailStr, constr

class Company_default(BaseModel):
    name: str
    vat: str
    email: EmailStr
    country_id: int
    phone: str
