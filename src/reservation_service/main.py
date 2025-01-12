from fastapi import FastAPI

from reservation_service.routers import api, manage

app = FastAPI(title="Reservation Service", version="1.0")


app.include_router(api.router)
app.include_router(manage.router)
