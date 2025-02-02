from datetime import datetime

from pydantic import BaseModel, EmailStr


class Company_default(BaseModel):
    company_type: int = 0
    name: str
    vat: str
    country_id: int = 31
    phone: str
    email: EmailStr


class Company_return(Company_default):
    company_id: int


class Opportunity_default(BaseModel):
    name: str
    contact_name: str
    x_studio_tese: str | None
    user_id: int
    team_id: int  
    tag_ids: list[int] = []  
    stage_id: int = 10

class Opportunity_return(Opportunity_default):
    opportunity_id: int

class PartnerNames(BaseModel):
    names: list[str]

class Config:
    extra = "allow"


class Message(BaseModel):
    message: str


class HealthCheck(BaseModel):
    status: str
    version: str
    timestamp: datetime
    uptime: float


class PingResponse(BaseModel):
    status: str
