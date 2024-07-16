from pydantic import BaseModel,Field
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class DecodedToken(BaseModel):
    user_id: int
    company_id: int
    department_id: int
    personal_id: str
    user_name: str
    storage: int
    permission: bool
    admin:bool
    icon: Optional[str] = Field(None) 
    expires: datetime

CSRF_KEY = "aaaaaaiuhlciakycbkaybciluabufchnlhaullbnubn1111u;h;uoho;h3uoh3;ounh"
class CsrfSettings(BaseModel):
  secret_key: str = CSRF_KEY
  cookie_samesite: str = "none"

class Csrf(BaseModel):
    csrf_token: str