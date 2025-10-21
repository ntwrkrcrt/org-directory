from pydantic import BaseModel, Field

from schemas.activity import ActivityResponse
from schemas.building import BuildingResponse
from schemas.phone import PhoneResponse


class OrganizationBase(BaseModel):
    name: str = Field(..., description="Organization name")
    building_id: int = Field(
        ..., description="Building ID where organization is located"
    )


class OrganizationResponse(OrganizationBase):
    id: int
    phones: list[PhoneResponse] = []
    activities: list[ActivityResponse] = []
    building: BuildingResponse

    model_config = {
        "from_attributes": True,
    }


class OrganizationListResponse(BaseModel):
    id: int
    name: str
    building_id: int

    model_config = {
        "from_attributes": True,
    }
