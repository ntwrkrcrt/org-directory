from typing import Optional

from pydantic import BaseModel, Field


class ActivityBase(BaseModel):
    name: str = Field(..., description="Activity name")
    parent_id: Optional[int] = Field(
        None, description="Parent activity ID for tree structure"
    )
    level: Optional[int] = Field(None, description="Nesting level (1-3)", ge=1, le=3)


class ActivityResponse(ActivityBase):
    id: int

    model_config = {
        "extra": "ignore",
        "populate_by_name": True,
        "from_attributes": True,
        "exclude_none": True,
    }


class ActivityTree(ActivityResponse):
    children: list["ActivityTree"] = []

    model_config = {
        "from_attributes": True,
    }
