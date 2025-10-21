from typing import Any, Optional, Sequence

from geoalchemy2 import Geography
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, selectinload

from models import Activity, Building, Organization


class CrudRepository:
    def __init__(self, session: AsyncSession):
        self.session: AsyncSession = session

    async def get_building_by_id(
        self,
        building_id: int,
    ) -> Optional[Building]:
        building_result = await self.session.execute(
            select(Building).where(Building.id == building_id)
        )
        return building_result.scalar_one_or_none()

    async def get_organizations_by_building(
        self,
        building_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Sequence[Organization]:
        result = await self.session.execute(
            select(Organization)
            .where(Organization.building_id == building_id)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_activity_by_id(self, activity_id: int) -> Optional[Activity]:
        activity_result = await self.session.execute(
            select(Activity).where(Activity.id == activity_id)
        )
        return activity_result.scalar_one_or_none()

    async def __get_activity_tree_ids(self, activity_id: int) -> list[int]:
        cte = (
            select(Activity.id, Activity.parent_id)
            .where(Activity.id == activity_id)
            .cte(name="activity_tree", recursive=True)
        )

        cte = cte.union_all(
            select(Activity.id, Activity.parent_id).where(
                Activity.parent_id == cte.c.id
            )
        )

        result = await self.session.execute(select(cte.c.id))

        return [row[0] for row in result.fetchall()]

    async def get_organizations_by_activity(
        self,
        activity_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Sequence[Organization]:
        activity_tree_ids: list[int] = await self.__get_activity_tree_ids(
            activity_id=activity_id,
        )
        result = await self.session.execute(
            select(Organization)
            .join(Organization.activities)
            .where(Activity.id.in_(activity_tree_ids))
            .distinct()
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_all_buldings(self) -> Sequence[Organization]:
        result = await self.session.execute(
            select(Organization).options(selectinload(Organization.building))
        )
        return result.scalars().all()

    async def get_organizations_by_area(
        self,
        min_latitude: float,
        max_latitude: float,
        min_longitude: float,
        max_longitude: float,
    ) -> Sequence[Organization]:
        make_envelope = func.ST_MakeEnvelope(
            min_longitude, min_latitude, max_longitude, max_latitude, 4326
        )
        result = await self.session.execute(
            select(Organization)
            .join(Organization.building)
            .where(
                Building.location.isnot(None),
                func.ST_Intersects(Building.location, make_envelope),
            )
            .options(selectinload(Organization.building))
        )
        return result.scalars().all()

    async def get_organization_by_id(
        self, organization_id: int
    ) -> Optional[Organization]:
        result = await self.session.execute(
            select(Organization)
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
            .where(Organization.id == organization_id)
        )
        return result.scalar_one_or_none()

    async def get_organization_by_name(self, name: str) -> Sequence[Organization]:
        result = await self.session.execute(
            select(Organization).where(Organization.name.ilike(f"%{name}%"))
        )
        return result.scalars().all()

    async def get_all_organizations(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Sequence[Organization]:
        result = await self.session.execute(
            select(Organization).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_activity_ids(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> list[tuple[Any]]:
        result = await self.session.execute(
            select(Activity.id, Activity.name).limit(limit).offset(offset)
        )
        return result.fetchall()

    async def get_all_buildings(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Sequence[Building]:
        result = await self.session.execute(
            select(Building).limit(limit).offset(offset)
        )
        return result.scalars().all()

    async def get_organizations_by_radius(
        self,
        latitude: float,
        longitude: float,
        radius_meters: float,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Sequence[Organization]:
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326).cast(
            Geography
        )
        result = await self.session.execute(
            select(Organization)
            .join(Organization.building)
            .where(
                Building.location.isnot(None),
                func.ST_DWithin(Building.location, point, radius_meters),
            )
            .order_by(func.ST_Distance(Building.location, point), Organization.id)
            .options(contains_eager(Organization.building))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_building_by_address(self, address: str) -> Optional[Building]:
        result = await self.session.execute(
            select(Building).where(Building.address.ilike(f"%{address}%"))
        )
        return result.scalar_one_or_none()
