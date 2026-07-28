from fastapi import APIRouter

from app.api.v1.access_requests import router as access_requests_router
from app.api.v1.assignments import router as assignments_router
from app.api.v1.auth import router as auth_router
from app.api.v1.contractors import router as contractors_router
from app.api.v1.employee_certificates import certification_levels_router
from app.api.v1.employee_certificates import router as employee_certificates_router
from app.api.v1.employees import router as employees_router
from app.api.v1.imports import router as imports_router
from app.api.v1.org import (
    cities_router,
    legal_entities_router,
    org_units_router,
    positions_router,
)
from app.api.v1.projects import objects_router, projects_router
from app.api.v1.public import router as public_router
from app.api.v1.remarks import router as remarks_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(public_router)
api_router.include_router(access_requests_router)
api_router.include_router(org_units_router)
api_router.include_router(positions_router)
api_router.include_router(cities_router)
api_router.include_router(legal_entities_router)
api_router.include_router(employees_router)
api_router.include_router(employee_certificates_router)
api_router.include_router(certification_levels_router)
api_router.include_router(projects_router)
api_router.include_router(objects_router)
api_router.include_router(contractors_router)
api_router.include_router(assignments_router)
api_router.include_router(remarks_router)
api_router.include_router(imports_router)
