from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/manage")


@router.get("/health")
def health_check():
    return HTMLResponse(status_code=200)
