# Routina Server

FastAPI 기반 루틴/알람 관리 서버 프로젝트

## Features

- 사용자 회원 관리 (이메일 로그인)
- 루틴(Routine) 생성/조회/수정/삭제
- 알람(Alarm) 생성/조회/수정/삭제 및 루틴 연결
- 루틴/알람 반복 요일 및 실행 기록 관리
- 통계 및 피드백(완료율, 주간/월간 리포트 등) 제공

## Tech Stack

- Python 3.10+
- FastAPI
- SQLAlchemy
- MySQL (pymysql)
- Pydantic

## Installation

1. **Clone the repository**

    ```bash
    git clone https://github.com/Team-RoutinA/routina-server-2.git
    cd routina-server-2
    ```

2. **Install requirements**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Database**

    - `database.py` 파일의 `DATABASE_URL`을 본인 환경에 맞게 수정하세요.

    ```python
    DATABASE_URL = "mysql+pymysql://root:<비밀번호>@localhost:3306/project"
    ```

4. **DB 테이블 생성**

    - 서버 첫 실행 시 자동으로 테이블이 생성됩니다.

5. **Run server**

    ```bash
    uvicorn main:app --reload
    ```

    - 기본: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (Swagger UI)

---

## API Overview

### Auth

- **POST /login**  
  이메일, 패스워드로 로그인 (임시: password는 'test' 고정)

### 루틴 관리

- **POST /routines**  
  루틴 생성

- **GET /routines**  
  루틴 목록 조회 (user-id header 필요)

- **PUT /routines/{routine_id}**  
  루틴 수정

- **DELETE /routines/{routine_id}**  
  루틴 삭제

### 알람 관리

- **POST /alarms**  
  알람 생성 및 루틴 연결

- **GET /alarms**  
  알람 전체 조회

- **GET /alarms/{alarm_id}**  
  특정 알람 상세

- **PUT /alarms/{alarm_id}**  
  알람 정보 수정

- **PATCH /alarms/{alarm_id}/status**  
  알람 활성/비활성 토글

- **DELETE /alarms/{alarm_id}**  
  알람 삭제

### 기타

- **GET /dashboard**  
  사용자별 대시보드 요약 정보

- **GET /routine-stats**  
  루틴별 완료율

- **GET /calendar?user_id=&year=&month=**  
  월별 루틴 달력 (일자별 성공률)

- **GET /weekly-feedback**  
  주간 피드백 요약

---

## Models

### User

| Field   | Type | Description |
|---------|------|-------------|
| user_id | str  | UUID        |
| email   | str  | Email       |
| name    | str  | Name        |

### Routine

| Field            | Type   | Description         |
|------------------|--------|---------------------|
| routine_id       | str    | UUID                |
| user_id          | str    | 사용자 ID           |
| title            | str    | 루틴 제목           |
| type             | str    | 루틴 타입           |
| goal_value       | int    | 목표값 (선택)       |
| duration_seconds | int    | 목표 시간(초, 선택) |
| deadline_time    | time   | 마감 시간(선택)     |
| success_note     | str    | 성공시 노트(선택)   |

### Alarm

| Field        | Type   | Description         |
|--------------|--------|---------------------|
| alarm_id     | str    | UUID                |
| user_id      | str    | 사용자 ID           |
| time         | time   | 알람 시간           |
| vibration_on | bool   | 진동 여부           |
| sound_volume | float  | 알람 볼륨           |
| status       | str    | Active/Inactive     |
| repeat_days  | str    | 반복 요일(문자열)   |

---

## 참고

- API 문서 자동 제공: `/docs`
- 주요 요청시 `user-id` 헤더 필요
