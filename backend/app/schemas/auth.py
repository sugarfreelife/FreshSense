from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # min 6 to match frontend; max 72 = bcrypt limit (longer input would 500 in passlib)
    password: str = Field(min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    id: str
    email: EmailStr

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Returned by register (auto-login) and login. Matches frontend AuthResponseSchema."""

    access_token: str
    token_type: str = "bearer"
    user: "UserOut"
