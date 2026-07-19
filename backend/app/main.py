"""Scaffold entrypoint for the UK Energy Grid Data & VPP Optimisation API.

Wires together the shared app configuration and each subproject's router.
Subproject routers are kept independent of one another; they only share
code via app.core.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dashboard, forecasting, health, vpp
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(forecasting.router)
app.include_router(vpp.router)
