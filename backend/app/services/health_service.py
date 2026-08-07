from app.schemas.health import ComponentStatus, SystemHealthResponse


class HealthService:
    def get_health(self) -> SystemHealthResponse:
        components = [
            ComponentStatus(name="api", status="ok"),
            ComponentStatus(name="frontend", status="ok"),
        ]
        return SystemHealthResponse(status="ok", version="0.1.0", components=components)
