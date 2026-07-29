from fastapi import APIRouter

from app.constants import APP_VERSION

router = APIRouter()


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": APP_VERSION}
