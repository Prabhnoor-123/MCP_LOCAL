from pydantic import BaseModel, EmailStr

class Registration(BaseModel):
    name: str
    email: EmailStr
    dob: str  