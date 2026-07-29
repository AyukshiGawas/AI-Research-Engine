from pydantic import BaseModel


class ComponentStatus(BaseModel):
    name: str
    status: str


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    components: list[ComponentStatus]
