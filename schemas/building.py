from pydantic import BaseModel, Field


class BuildingBase(BaseModel):
    address: str = Field(..., description="Building address")
    latitude: float = Field(..., description="Latitude coordinate", ge=-90, le=90)
    longitude: float = Field(..., description="Longitude coordinate", ge=-180, le=180)


class BuildingResponse(BuildingBase):
    id: int

    model_config = {
        "from_attributes": True,
    }
