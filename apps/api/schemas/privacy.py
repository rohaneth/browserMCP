from pydantic import BaseModel


class PauseStatusResponse(BaseModel):
    status: str
    is_paused: bool
    message: str


class DeleteEventResponse(BaseModel):
    status: str
    message: str


class DeleteDateRangeResponse(BaseModel):
    status: str
    deleted_count: int
    message: str
