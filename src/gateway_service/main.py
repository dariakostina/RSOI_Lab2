from fastapi import FastAPI

from gateway_service.routers import api, manage

app = FastAPI(title="Library System Gateway", version="1.0")

app.include_router(api.router)
app.include_router(manage.router)
