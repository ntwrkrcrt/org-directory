from pydantic import BaseModel, Field


class PhoneBase(BaseModel):
    number: str = Field(..., description="Phone number")


class PhoneResponse(PhoneBase):
    id: int
    organization_id: int

    model_config = {
        "from_attributes": True,
    }
