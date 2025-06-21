from pydantic import BaseModel
from datetime import datetime

class SensorDataPayload(BaseModel):
    value: float
    timestamp: datetime

class CalibrationRequest(BaseModel):
    gain: float
    offset: float

class CalibrationResponse(BaseModel):
    status: int

class StatusMessage(BaseModel):
    uptime: int
    error_code: int
    timestamp: datetime
