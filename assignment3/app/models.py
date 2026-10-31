from pydantic import BaseModel, Field


class CallCompleted(BaseModel):
    account_id: str = Field(min_length=1)
    disposition: str
    attempt: int = Field(default=0, ge=0)


class HealthResponse(BaseModel):
    status: str
