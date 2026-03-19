from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    password: str
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    nome: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }
    
class ChatRequest(BaseModel):
    message: str
    conversation_id: int
