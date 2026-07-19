"""Energy price forecasting via quantile regression.

This subproject will eventually expose endpoints that serve quantile
regression forecasts of energy prices (e.g. predicted price bands at
different quantiles), along with the model's real-world interpretation.
For now it only exposes a placeholder endpoint.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"subproject": "forecasting", "status": "placeholder"}
