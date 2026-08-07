from fastapi import APIRouter

root_router = APIRouter()
versioned_router = APIRouter()


@root_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@versioned_router.get("/health")
def versioned_health() -> dict[str, str]:
    return {"status": "ok"}


@versioned_router.get("/health/liveness")
def liveness() -> dict[str, str]:
    return {"status": "alive"}
