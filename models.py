from sqlalchemy import Column, String, Integer, Time, Text, ForeignKey, DECIMAL
from sqlalchemy.dialects.mysql import CHAR
from database import Base
import uuid

class AppUser(Base):
    __tablename__ = "app_user"
    user_id = Column(CHAR(36), primary_key=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=True)

class Routine(Base):
    __tablename__ = "routine"
    routine_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("app_user.user_id"), nullable=False)
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)
    goal_value = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    deadline_time = Column(Time, nullable=True)
    success_note = Column(Text, nullable=True)

class Alarm(Base):
    __tablename__ = "alarm"
    alarm_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(CHAR(36), ForeignKey("app_user.user_id"), nullable=False)
    time = Column(Time, nullable=False)
    sound_volume = Column(DECIMAL(3, 2), nullable=False, default=0.8)
    status = Column(String(20), default='Active')

class AlarmRoutine(Base):
    __tablename__ = "alarm_routine"
    alr_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alarm_id = Column(CHAR(36), ForeignKey("alarm.alarm_id"), nullable=False)
    routine_id = Column(CHAR(36), ForeignKey("routine.routine_id"), nullable=False)
    order = Column(Integer, nullable=False)

class AlarmRepeatDay(Base):
    __tablename__ = "alarm_repeat_day"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alarm_id = Column(CHAR(36), ForeignKey("alarm.alarm_id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 1=Mon ~ 7=Sun
class AlarmExecutionLog(Base):
    __tablename__ = "alarm_exec_log"
    exec_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alarm_id = Column(CHAR(36), ForeignKey("alarm.alarm_id"), nullable=False)
    scheduled_ts = Column(String(32))
    dismissed_ts = Column(String(32))
    total_routines = Column(Integer, nullable=False)
    completed_routines = Column(Integer, nullable=False)
    success_rate = Column(DECIMAL(4, 3), nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS | PARTIAL | ABORTED | MISSED

class AlarmExecutionRoutine(Base):
    __tablename__ = "alarm_exec_routine"
    axr_id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    exec_id = Column(CHAR(36), ForeignKey("alarm_exec_log.exec_id"), nullable=False)
    routine_id = Column(CHAR(36), ForeignKey("routine.routine_id"), nullable=False)
    completed = Column(Integer, nullable=False)  # 1=Y, 0=N
    actual_value = Column(Integer, nullable=True)
    completed_ts = Column(String(32))
    abort_ts = Column(String(32))
    order = Column(Integer, nullable=False)