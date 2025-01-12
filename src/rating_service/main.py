from fastapi import FastAPI

from rating_service.routers import api, manage

app = FastAPI(title="Rating Service", version="1.0")


app.include_router(api.router)
app.include_router(manage.router)
