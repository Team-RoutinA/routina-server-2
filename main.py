from fastapi import FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models, schemas
import uuid
from typing import List
from pydantic import BaseModel
from datetime import time as time_type
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ✅ 로그인 엔드포인트 (고정된 계정 검증)
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/login")
def login(req: LoginRequest):
    if req.email == "test@gmail.com" and req.password == "test":
        return {"user_id": "test"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/routines", response_model=schemas.RoutineOut)
def create_routine(routine: schemas.RoutineCreate, db: Session = Depends(get_db)):
    deadline_time_obj = (
    datetime.strptime(routine.deadline_time + ":00", "%H:%M:%S").time()
    if routine.deadline_time else None
)

    db_routine = models.Routine(
        routine_id=str(uuid.uuid4()),
        user_id=routine.user_id,
        title=routine.title,
        type=routine.type,
        goal_value=routine.goal_value,
        duration_seconds=routine.duration_seconds,
        deadline_time=deadline_time_obj,
        success_note=routine.success_note
    )
    db.add(db_routine)
    db.commit()
    db.refresh(db_routine)

    # ✅ deadline_time을 문자열로 바꿔서 리턴
    return {
        "routine_id": db_routine.routine_id,
        "user_id": db_routine.user_id,
        "title": db_routine.title,
        "type": db_routine.type,
        "goal_value": db_routine.goal_value,
        "duration_seconds": db_routine.duration_seconds,
        "deadline_time": db_routine.deadline_time.strftime("%H:%M") if db_routine.deadline_time else None,
        "success_note": db_routine.success_note
    }

router = APIRouter()
@router.get("/routines", response_model=List[schemas.RoutineOut])
def get_routines(db: Session = Depends(get_db)):
    db_routines = db.query(models.Routine).all()
    
    # deadline_time이 datetime.time -> str로 변환
    routines_out = []
    for routine in db_routines:
        routines_out.append({
            "routine_id": routine.routine_id,
            "user_id": routine.user_id,
            "title": routine.title,
            "type": routine.type,
            "goal_value": routine.goal_value,
            "duration_seconds": routine.duration_seconds,
            "deadline_time": routine.deadline_time.strftime("%H:%M") if routine.deadline_time else None,
            "success_note": routine.success_note
        })
    
    return routines_out
@app.post("/alarms", response_model=schemas.AlarmOut)
def create_alarm(alarm: schemas.AlarmCreate, db: Session = Depends(get_db)):
    alarm_id = str(uuid.uuid4())
    time_obj = time_type.fromisoformat(alarm.time)
    db_alarm = models.Alarm(
        alarm_id=alarm_id,
        user_id=alarm.user_id,
        time=alarm.time if isinstance(alarm.time, time_type) else time_type.fromisoformat(alarm.time),
        status=alarm.status,
        sound_volume=alarm.sound_volume if alarm.sound_volume is not None else 0.8,
        repeat_days=','.join(map(str, alarm.repeat_days or []))
    )
    db.add(db_alarm)
    db.commit()

    for r in alarm.routines:
        db.add(models.AlarmRoutine(
            alr_id=str(uuid.uuid4()),
            alarm_id=alarm_id,
            routine_id=r.routine_id,
            order=r.order
        ))
    db.commit()
    for wd in alarm.repeat_days:
        db.add(models.AlarmRepeatDay(
            id=str(uuid.uuid4()),
            alarm_id=alarm_id,
            weekday=wd
        ))
    db.commit()

    return {
        "alarm_id": alarm_id,
        "time": alarm.time.strftime("%H:%M") if isinstance(alarm.time, time_type) else alarm.time,
        "status": db_alarm.status,
        "sound_volume": alarm.sound_volume,
        "routines": alarm.routines,
        "repeat_days": alarm.repeat_days
    }

@app.post("/alarms/{alarm_id}/repeat-days", response_model=List[schemas.AlarmRepeatDayOut])
def set_alarm_repeat_days(
    alarm_id: str = Path(...),
    req: schemas.AlarmRepeatDaysIn = None,
    db: Session = Depends(get_db)
):
    db.query(models.AlarmRepeatDay).filter(models.AlarmRepeatDay.alarm_id == alarm_id).delete()
    entries = []
    for wd in req.repeat_days:
        entry = models.AlarmRepeatDay(
            id=str(uuid.uuid4()),
            alarm_id=alarm_id,
            weekday=wd
        )
        db.add(entry)
        entries.append(entry)
    db.commit()
    return entries

@app.get("/dashboard")
def get_dashboard(user_id: str, db: Session = Depends(get_db)):
    alarms = db.query(models.Alarm).filter(models.Alarm.user_id == user_id).all()
    result = []
    for alarm in alarms:
        ar_links = db.query(models.AlarmRoutine).filter(models.AlarmRoutine.alarm_id == alarm.alarm_id).order_by(models.AlarmRoutine.order).all()
        routines = []
        for link in ar_links:
            r = db.query(models.Routine).filter(models.Routine.routine_id == link.routine_id).first()
            if r:
                routines.append(r)
        repeat_days = db.query(models.AlarmRepeatDay.weekday).filter(models.AlarmRepeatDay.alarm_id == alarm.alarm_id).all()
        weekdays = [row.weekday for row in repeat_days]
        result.append({
            "alarm_id": alarm.alarm_id,
            "time": alarm.time.strftime("%H:%M") if alarm.time else None,
            "status": alarm.status,
            "repeat_days": weekdays,
            "routines": [r.__dict__ for r in routines]
        })
    all_routines = db.query(models.Routine).filter(models.Routine.user_id == user_id).all()
    return {
        "alarms": result,
        "routines": [r.__dict__ for r in all_routines]
    }
@app.put("/routines/{routine_id}", response_model=schemas.RoutineOut)
def update_routine(
    routine_id: str,
    update: schemas.RoutineCreate,  # or RoutineUpdate if you made separate schema
    db: Session = Depends(get_db)
):
    r = db.query(models.Routine).filter(
        models.Routine.routine_id == routine_id,
        models.Routine.user_id == update.user_id
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Routine not found")

    # ⏰ deadline_time 변환
    if update.deadline_time:
        try:
            deadline_time_obj = datetime.strptime(update.deadline_time, "%H:%M").time()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use 'HH:MM'.")
    else:
        deadline_time_obj = None

    # 📌 deadline_time은 수동으로 먼저 설정
    r.deadline_time = deadline_time_obj

    # 🧹 user_id는 변경하지 않도록 제거
    update_data = update.dict()
    update_data.pop("user_id", None)
    update_data.pop("deadline_time", None)  # 이미 따로 처리했으므로 제외

    # 🔁 나머지 필드 업데이트
    for key, value in update_data.items():
        setattr(r, key, value)

    db.commit()
    db.refresh(r)

    # ⏎ 응답 모델 반환 (자동 변환)
    return {
        "routine_id": r.routine_id,
        "user_id": r.user_id,
        "title": r.title,
        "type": r.type,
        "goal_value": r.goal_value,
        "duration_seconds": r.duration_seconds,
        "deadline_time": r.deadline_time.strftime("%H:%M") if r.deadline_time else None,
        "success_note": r.success_note,
    }


# 루틴 삭제
@app.delete("/routines/{routine_id}")
def delete_routine(routine_id: str, req: schemas.RoutineDelete, db: Session = Depends(get_db)):
    db.query(models.Routine).filter(models.Routine.routine_id == routine_id, models.Routine.user_id == req.user_id).delete()
    db.commit()
    return {"message": "Routine deleted"}

# 알람 삭제
@app.delete("/alarms/{alarm_id}")
def delete_alarm(alarm_id: str, req: schemas.AlarmDelete, db: Session = Depends(get_db)):
    db.query(models.AlarmRoutine).filter(models.AlarmRoutine.alarm_id == alarm_id).delete()
    db.query(models.Alarm).filter(models.Alarm.alarm_id == alarm_id, models.Alarm.user_id == req.user_id).delete()
    db.commit()
    return {"message": "Alarm deleted"}

# 수행 기록 저장
@app.post("/alarm-executions")
def save_alarm_execution(data: schemas.AlarmExecutionCreate, db: Session = Depends(get_db)):
    exec_id = str(uuid.uuid4())
    total = len(data.routines)
    completed = sum(1 for r in data.routines if r.completed)
    rate = round(completed / total, 3) if total > 0 else 0.0
    status = "SUCCESS" if completed == total else ("PARTIAL" if completed > 0 else "ABORTED")

    log = models.AlarmExecutionLog(
        exec_id=exec_id,
        alarm_id=data.alarm_id,
        scheduled_ts=data.scheduled_ts,
        dismissed_ts=data.dismissed_ts,
        total_routines=total,
        completed_routines=completed,
        success_rate=rate,
        status=status
    )
    db.add(log)
    db.commit()

    for r in data.routines:
        detail = models.AlarmExecutionRoutine(
            axr_id=str(uuid.uuid4()),
            exec_id=exec_id,
            routine_id=r.routine_id,
            completed=int(r.completed),
            actual_value=r.actual_value,
            completed_ts=r.completed_ts,
            abort_ts=r.abort_ts,
            order=r.order
        )
        db.add(detail)
    db.commit()
    return {"message": "Execution saved", "exec_id": exec_id}

# 루틴 통계 요약 (완료율)
@app.get("/routine-stats")
def routine_stats(user_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import func
    data = db.query(
        models.Routine.title,
        func.count(models.AlarmExecutionRoutine.axr_id).label("total"),
        func.sum(models.AlarmExecutionRoutine.completed).label("done")
    ).join(models.AlarmExecutionRoutine, models.Routine.routine_id == models.AlarmExecutionRoutine.routine_id).filter(models.Routine.user_id == user_id).group_by(models.Routine.title).all()
    return [
        {"title": title, "done": int(done or 0), "total": total, "rate": round(done / total, 2) if total > 0 else 0.0}
        for title, total, done in data
    ]
@app.patch("/alarms/{alarm_id}/status")
def update_alarm_status(alarm_id: str, status: str, db: Session = Depends(get_db)):
    alarm = db.query(models.Alarm).filter(models.Alarm.alarm_id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm.status = status
    db.commit()
    return {"message": f"Alarm status updated to {status}"}

# 알람 전체 조회
@app.get("/alarms", response_model=List[schemas.AlarmOut])
def get_alarms(user_id: str, db: Session = Depends(get_db)):
    alarms = db.query(models.Alarm).filter(models.Alarm.user_id == user_id).all()
    result = []
    for alarm in alarms:
        routines = db.query(models.AlarmRoutine).filter(models.AlarmRoutine.alarm_id == alarm.alarm_id).order_by(models.AlarmRoutine.order).all()
        result.append({
            "alarm_id": alarm.alarm_id,
            "time": alarm.time.strftime("%H:%M"),
            "status": alarm.status,
            "sound_volume": alarm.sound_volume,
            "repeat_days": list(map(int, alarm.repeat_days.split(','))) if alarm.repeat_days else [],
            "routines": [{"routine_id": r.routine_id, "order": r.order} for r in routines]
        })
    return result

# 특정 알람 조회
@app.get("/alarms/{alarm_id}")
def get_alarm_detail(alarm_id: str, db: Session = Depends(get_db)):
    alarm = db.query(models.Alarm).filter(models.Alarm.alarm_id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    repeat_days = db.query(models.AlarmRepeatDay.weekday).filter(models.AlarmRepeatDay.alarm_id == alarm_id).all()
    routines = db.query(models.AlarmRoutine).filter(models.AlarmRoutine.alarm_id == alarm_id).order_by(models.AlarmRoutine.order).all()
    routine_list = []
    for r in routines:
        rt = db.query(models.Routine).filter(models.Routine.routine_id == r.routine_id).first()
        if rt:
            routine_list.append({
                "routine_id": rt.routine_id,
                "user_id": rt.user_id,
                "title": rt.title,
                "type": rt.type,
                "goal_value": rt.goal_value,
                "duration_seconds": rt.duration_seconds,
                "deadline_time": rt.deadline_time.strftime("%H:%M") if rt.deadline_time else None,
                "success_note": rt.success_note
            })

    return {
        "alarm_id": alarm.alarm_id,
        "time": alarm.time.strftime("%H:%M") if alarm.time else None,
        "status": alarm.status,
        "repeat_days": [r[0] for r in repeat_days],  # 수정
        "routines": routine_list
    }

# 월별 루틴 성공률 달력 (일자별 수행률)
@app.get("/calendar")
def calendar_view(user_id: str, year: int, month: int, db: Session = Depends(get_db)):
    from sqlalchemy import extract, func
    results = db.query(
        func.date(models.AlarmExecutionLog.scheduled_ts).label("date"),
        func.avg(models.AlarmExecutionLog.success_rate).label("avg_rate")
    ).join(models.Alarm, models.Alarm.alarm_id == models.AlarmExecutionLog.alarm_id).filter(
        models.Alarm.user_id == user_id,
        extract("year", models.AlarmExecutionLog.scheduled_ts) == year,
        extract("month", models.AlarmExecutionLog.scheduled_ts) == month
    ).group_by("date").all()
    return [{"date": str(r.date), "success_rate": float(round(r.avg_rate, 2))} for r in results]

# 주간 피드백 요약
@app.get("/weekly-feedback")
def weekly_feedback(user_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import func, text
    results = db.execute(text("""
        SELECT
            WEEK(scheduled_ts, 1) as week_num,
            COUNT(*) as total,
            SUM(completed_routines) as done,
            ROUND(SUM(completed_routines)/SUM(total_routines), 2) as rate
        FROM alarm_exec_log
        JOIN alarm ON alarm_exec_log.alarm_id = alarm.alarm_id
        WHERE alarm.user_id = :uid
        GROUP BY week_num
        ORDER BY week_num DESC
        LIMIT 4
    """), {"uid": user_id}).fetchall()
    return [
        {"week": r[0], "done": r[1], "completed": int(r[2] or 0), "rate": float(r[3] or 0)} for r in results
    ]
# 알람 수정 + 반복 요일도 함께 수정
@app.put("/alarms/{alarm_id}")
def update_alarm(alarm_id: str, update: schemas.AlarmUpdate, db: Session = Depends(get_db)):
    alarm = db.query(models.Alarm).filter(models.Alarm.alarm_id == alarm_id, models.Alarm.user_id == update.user_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    if update.time:
        alarm.time = time_type.fromisoformat(update.time)
    if update.status:
        alarm.status = update.status
    if update.sound_volume is not None:
        alarm.sound_volume = update.sound_volume
    if update.repeat_days is not None:
        alarm.repeat_days = ','.join(map(str, update.repeat_days))
    db.commit()
    return {"message": "Alarm updated", "alarm_id": alarm_id, "repeat_days": update.repeat_days}

# 알람 실행 결과 루틴별 업데이트 (PUT)
@app.put("/alarm-executions/{exec_id}")
def update_alarm_execution(exec_id: str, data: dict, db: Session = Depends(get_db)):
    log = db.query(models.AlarmExecutionLog).filter(models.AlarmExecutionLog.exec_id == exec_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Execution not found")
    routines = data.get("routines", [])
    completed = 0
    for r in routines:
        axr = db.query(models.AlarmExecutionRoutine).filter(
            models.AlarmExecutionRoutine.exec_id == exec_id,
            models.AlarmExecutionRoutine.routine_id == r["routine_id"]
        ).first()
        if axr:
            axr.completed = int(r["completed"])
            axr.actual_value = r.get("actual_value")
            axr.completed_ts = r.get("completed_ts")
            axr.abort_ts = r.get("abort_ts")
            completed += int(r["completed"])

    log.completed_routines = completed
    log.success_rate = round(completed / log.total_routines, 3)
    log.status = "SUCCESS" if completed == log.total_routines else ("PARTIAL" if completed > 0 else "ABORTED")
    db.commit()

    updated = db.query(models.AlarmExecutionRoutine).filter(models.AlarmExecutionRoutine.exec_id == exec_id).all()
    return {
        "exec_id": exec_id,
        "alarm_id": log.alarm_id,
        "status": log.status,
        "total_routines": log.total_routines,
        "completed_routines": log.completed_routines,
        "success_rate": log.success_rate,
        "routine_execution_details": [r.__dict__ for r in updated]
    }
app.include_router(router)
