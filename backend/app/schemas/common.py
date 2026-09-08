from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    service: str = "freshsense-ai"


class MessageOut(BaseModel):
    message: str
