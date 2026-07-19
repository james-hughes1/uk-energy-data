"""Live UK power grid dashboard.

This subproject will eventually expose endpoints that pull live and historical
grid data (e.g. imbalance price, national demand) from sources such as
Elexon/BMRS or the National Grid ESO Data Portal, for display on the
dashboard tab. For now it only exposes a placeholder endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"subproject": "dashboard", "status": "placeholder"}
