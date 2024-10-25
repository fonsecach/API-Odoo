from datetime import datetime

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


class Opportunity_default(BaseModel):
    partner_id: int
    name: str
    x_studio_tese: str
    stage_id: int
    user_id: int
    x_studio_omie_id: str
    #x_studio_criao_no_omie: datetime # ajustar o datetime, o oddo não aceita


class Opportunity_return(Opportunity_default):
    opportunity_id: int
