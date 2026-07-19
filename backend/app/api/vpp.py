"""Virtual power plant (VPP) optimisation.

This subproject will eventually expose endpoints that run an optimisation
model (e.g. battery dispatch scheduling) to maximise the value of a virtual
power plant given price forecasts and asset constraints. For now it only
exposes a placeholder endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/vpp", tags=["vpp"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"subproject": "vpp", "status": "placeholder"}
