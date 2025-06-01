from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import time


class RoutineCreate(BaseModel):
    user_id: str
    title: str
    type: str
    goal_value: Optional[int] = None
    duration_seconds: Optional[int] = None
    deadline_time: Optional[str] = None
    success_note: Optional[str] = None

class RoutineOut(RoutineCreate):
    routine_id: str

class AlarmRoutineLink(BaseModel):
    routine_id: str
    order: int
class AlarmRoutineIn(BaseModel):
    routine_id: str
    order: int
class AlarmCreate(BaseModel):
    user_id: str
    time: str
    status: str
    sound_volume: Optional[float] = Field(default=0.8)
    repeat_days: Optional[list[int]] = []
    routines: list["AlarmRoutineIn"]

class AlarmUpdate(BaseModel):
    user_id: str
    time: Optional[str]
    status: Optional[str]
    sound_volume: Optional[float]
    repeat_days: Optional[List[int]] = []

class AlarmOut(BaseModel):
    alarm_id: str
    time: str
    status: str
    routines: List[RoutineOut]

class AlarmRepeatDaysIn(BaseModel):
    alarm_id: str
    repeat_days: List[int]  # 1 ~ 7

class AlarmRepeatDayOut(BaseModel):
    alarm_id: str
    weekday: int
class ExecutionRoutine(BaseModel):
    routine_id: str
    completed: bool
    actual_value: Optional[int] = None
    completed_ts: Optional[str] = None
    abort_ts: Optional[str] = None
    order: int

class AlarmExecutionCreate(BaseModel):
    alarm_id: str
    scheduled_ts: str
    dismissed_ts: str
    routines: List[ExecutionRoutine]

class RoutineUpdate(RoutineCreate):
    pass

class RoutineDelete(BaseModel):  
    user_id: str
class AlarmDelete(BaseModel):
    user_id: str
class AlarmRoutineOut(BaseModel):
    routine_id: str
    order: int

class AlarmOut(BaseModel):
    alarm_id: str
    time: str
    status: str
    sound_volume: float
    repeat_days: List[int]
    routines: List[AlarmRoutineOut]
