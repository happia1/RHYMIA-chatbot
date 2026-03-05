# 에이전트 기반 지능형 스케줄러 통합 전략

기존 RHYMIA 서비스의 스케줄러 기능을 **Next.js + LangGraph 에이전트**로 업그레이드하기 위한 구체적인 통합 전략입니다.

---

## 1. RHYMIA 스케줄러 UI의 '에이전트 지능화' 포인트

단순히 일정을 보여주는 화면에 **에이전트의 사고 과정**을 녹여내면 사용자 경험(UX)이 극대화됩니다.

| 포인트 | 설명 | 구현 방향 |
|--------|------|------------|
| **실시간 분석 피드백** | 사진을 올리면 "에이전트가 준비물을 파악 중입니다..."처럼 **현재 진행 중인 노드(Plan → Execute → Refine)**를 시각적으로 보여줍니다. | 업로드 후 API 호출 중 클라이언트에서 단계별 메시지 표시(또는 서버 스트리밍). Plan → Execute → Refine 순서로 스텝 인디케이터 + 짧은 문구 노출. |
| **지능형 To-Do 연동** | 일정만 등록되는 게 아니라, **하단 To-Do 섹션**에 "내일 소풍 도시락 재료 사기" 같은 **할 일이 자동 생성**되어 **체크박스**로 나타납니다. | 에이전트가 반환한 `extracted.todo_list`를 그대로 To-Do 블록에 바인딩. 일정 카드 하단 또는 별도 "이 일정을 위한 할 일" 섹션에 체크 가능한 리스트로 렌더링. |
| **에이전트 채팅 인터페이스** | Refine 노드에서 정보가 부족할 때, **스케줄러 화면 상단**에 에이전트가 "어머니, 등원 시간이 안 적혀 있는데 혹시 평소처럼 9시인가요?"처럼 **다정하게 질문**하도록 구성합니다. | `interrupt` 응답 시 상단에 말풍선/카드 형태로 질문 문구 표시 + 입력창 + "보내기". 사용자 입력으로 `/api/scheduler/resume` 호출 후 완료 시 일정 반영 및 To-Do 표시. |

이 세 가지를 스케줄러 화면(예: `dashboard/plan/schedule`)에 통합하면, "사진만 올리면 에이전트가 알아서 일정·할 일까지 챙겨 준다"는 인상을 줄 수 있습니다.

**구현된 UI 위치 (rhymia-mvp)**  
- **스케줄 페이지**: `app/dashboard/plan/schedule/page.tsx` — 상단에 `SchedulerAgentBlock` 배치.  
- **에이전트 블록**: `components/scheduler/SchedulerAgentBlock.tsx` — 업로드 + 단계 피드백 + Refine 채팅 + 완료 시 To-Do.  
- **실시간 분석 피드백**: `components/scheduler/AgentStepFeedback.tsx` — Plan / Execute / Refine 단계 메시지.  
- **지능형 To-Do**: `components/scheduler/AgentTodoSection.tsx` — `todo_list` 체크박스.  
- **에이전트 채팅**: `components/scheduler/AgentChatBubble.tsx` — Refine 질문 + 입력 + 보내기.  
- **API 클라이언트**: `lib/scheduler-api.ts` — `extractSchedule`, `resumeSchedule`.  
- **BFF**: `app/api/scheduler/extract/route.ts`, `app/api/scheduler/resume/route.ts`.

---

## 2. 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        RHYMIA 프론트 (Next.js)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │ 스케줄러 화면  │  │ 사진/텍스트   │  │ API Route (BFF)              │   │
│  │ (일정 목록)   │←─│ 업로드 UI    │→─│ /api/scheduler/extract        │   │
│  └──────┬───────┘  └──────────────┘  │ /api/scheduler/resume         │   │
│         │                             └──────────────┬───────────────┘   │
│         │                                            │                   │
│         │  DB 조회 (일정 목록)                         │ fetch/axios       │
│         ↓                                            ↓                   │
│  ┌──────────────┐                             ┌─────────────────────┐   │
│  │ PostgreSQL   │                             │ 에이전트 서버        │   │
│  │ (schedules)  │←── 저장 요청 (완료 시) ──────│ (FastAPI + LangGraph)│   │
│  └──────────────┘                             │ RHYMIA-scheduler    │   │
└─────────────────────────────────────────────────────────────────────────┘  │
                                                                              │
                                    Plan → Execute → Refine → (저장 시 DB)    │
```

- **백엔드 분리(Microservice)**: LangGraph 에이전트는 **Python FastAPI 서버**로 운영하고, Next.js는 해당 서버를 **fetch/axios**로 호출합니다.
- **BFF(Backend For Frontend)**: Next.js **API Route**가 업로드 수신 → 에이전트 서버 호출 → DB 저장까지 오케스트레이션합니다.

---

## 3. 데이터 흐름 (상세)

| 단계 | 담당 | 설명 |
|------|------|------|
| 1 | 사용자 | RHYMIA 앱에서 유치원 가정통신문 **사진 업로드** 또는 **일정 텍스트 입력** |
| 2 | Next.js | API Route가 multipart(base64)로 받은 이미지/텍스트를 **에이전트 서버로 전달** |
| 3 | FastAPI + LangGraph | **Plan → Execute → Refine** 수행. 날짜/시간 없으면 `interrupt`로 질문 반환 |
| 4 | Next.js | 응답이 **정제된 JSON**이면 DB(PostgreSQL)에 저장; **interrupt**면 클라이언트에 질문 전달 |
| 5 | 클라이언트 | interrupt 시 사용자에게 "날짜/시간을 알려주세요" 표시 → 사용자 입력 시 **resume API** 호출 |
| 6 | 스케줄러 화면 | DB에서 일정 목록 조회 후 **캘린더/리스트**로 표시 |

---

## 4. API 설계

### 4.1 에이전트 서버 (FastAPI, RHYMIA-scheduler)

| 메서드 | 경로 | 용도 | 요청 | 응답 |
|--------|------|------|------|------|
| POST | `/scheduler/extract` | 사진 또는 텍스트로 일정 추출 시작 | `user_text?`, `image_base64?`, `thread_id?` | `extracted` + `saved_path` 또는 `__interrupt__` |
| POST | `/scheduler/resume` | Refine에서 멈춘 뒤 사용자 답변으로 재개 | `thread_id`, `user_reply` | 동일 |

- **요청**: `user_text`(선택), `image_base64`(선택, data URL 또는 base64 문자열), `thread_id`(선택, 기본값 생성 가능).
- **응답**  
  - 완료: `{ "extracted": {...}, "saved_path": "...", "schedules": [...] }`  
  - interrupt: `{ "__interrupt__": "일정의 날짜나 시간을 알려주세요. (예: 3월 15일 오후 2시)" }`  
  - 재개 후 완료: 위와 동일한 완료 형태.

### 4.2 Next.js API Route (BFF)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/scheduler/extract` | FormData(이미지 파일 또는 text 필드) 수신 → 에이전트 `/scheduler/extract` 호출 → 완료 시 DB 저장 후 결과 반환 |
| POST | `/api/scheduler/resume` | `thread_id`, `user_reply` 수신 → 에이전트 `/scheduler/resume` 호출 → 완료 시 DB 저장 후 결과 반환 |
| GET | `/api/scheduler/list` | DB에서 해당 사용자(또는 가족) 일정 목록 조회 (스케줄러 화면용) |

- DB 저장은 **에이전트가 반환한 `extracted`(또는 최종 일정 객체)**를 그대로 또는 매핑해서 PostgreSQL에 insert합니다.

---

## 5. DB 스키마 제안 (PostgreSQL)

에이전트가 반환하는 JSON 구조에 맞춘 테이블 예시입니다.

```sql
-- 일정 한 건 (에이전트 추출 결과와 1:1 매핑)
CREATE TABLE schedules (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     TEXT NOT NULL,                    -- RHYMIA 사용자(또는 가족) 식별자
  thread_id   TEXT,                             -- 에이전트 thread (interrupt 재개 시 필요, 선택)

  -- 에이전트 추출 필드
  date        TEXT NOT NULL DEFAULT '',         -- 날짜 (예: 3월 15일)
  time        TEXT NOT NULL DEFAULT '',         -- 시간 (예: 오후 2시)
  title       TEXT NOT NULL DEFAULT '',         -- 일정명
  materials   JSONB DEFAULT '[]',              -- 준비물 문자열 배열
  memo        TEXT NOT NULL DEFAULT '',        -- 부모가 알아야 할 추가 정보 요약
  todo_list   JSONB DEFAULT '[]',              -- 미리 할 일 리스트

  -- 프로젝트 분류 (에이전트 판별 + Next.js 필터·컬러 코딩)
  project_type TEXT NOT NULL DEFAULT 'GENERAL', -- KIDS | FINANCE | GENERAL
  ui_color     TEXT NOT NULL DEFAULT '#64748B', -- 캘린더 색 (자녀 #FFB6C1, 재무 #3B82F6)
  project_id   TEXT NOT NULL DEFAULT '',        -- PROJ_KIDS_001, PROJ_FINANCE_001 등
  tag          TEXT NOT NULL DEFAULT '',        -- Child, Finance, General

  created_at  TIMESTAMPTZ DEFAULT now(),
  updated_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_schedules_user_id ON schedules(user_id);
CREATE INDEX idx_schedules_created_at ON schedules(created_at);
CREATE INDEX idx_schedules_project_type ON schedules(project_type);
```

- Next.js에서 에이전트 응답의 `rhymia_schedule`(또는 `extracted`+변환)를 위 컬럼에 매핑해 insert/update하면 됩니다.
- **필터링**: `WHERE project_type = 'KIDS'` 등으로 '자녀 프로젝트만 보기' 구현. **시각적 분리**: `ui_color`로 캘린더/대시보드 색상 구분.

---

## 6. 구현 체크리스트

### 6.1 RHYMIA-scheduler (Python)

- [ ] **FastAPI 앱** 추가: `POST /scheduler/extract`, `POST /scheduler/resume` 구현.
- [ ] 이미지 수신: multipart 또는 JSON body의 `image_base64`(data URL 포함)를 에이전트 `run_agent(image_path=...)`에 전달.
- [ ] **저장 연동 선택**:  
  - A) 에이전트는 기존처럼 `data/schedules.json`만 저장하고, Next.js가 완료 응답을 받은 뒤 **Next.js에서 DB에 저장**.  
  - B) FastAPI에서 PostgreSQL 직접 연결해, 에이전트 완료 시 DB에 insert (구현 복잡도 증가).
- 권장: **A**. 에이전트 서버는 “추출 + 정제”만 담당하고, 영구 저장은 Next.js + DB가 담당.

### 6.2 Next.js (rhymia-mvp)

- [ ] **API Route**  
  - `app/api/scheduler/extract/route.ts`: FormData/JSON 수신 → 에이전트 서버 `POST /scheduler/extract` 호출 → `__interrupt__`면 그대로 반환, 완료면 DB 저장 후 `extracted`/일정 정보 반환.  
  - `app/api/scheduler/resume/route.ts`: `thread_id`, `user_reply` 전달 → 에이전트 서버 `POST /scheduler/resume` 호출 → 완료 시 DB 저장 후 반환.  
  - `app/api/scheduler/list/route.ts`: DB에서 일정 목록 조회 (user_id 등으로 필터).
- [ ] **환경 변수**: `SCHEDULER_AGENT_URL=http://localhost:8000` (에이전트 서버 주소).
- [ ] **스케줄러 화면**: 기존 스케줄러 UI가 `GET /api/scheduler/list`로 목록을 가져와 캘린더/리스트에 표시.
- [ ] **업로드 UI**: 사진 또는 텍스트 입력 → `POST /api/scheduler/extract` 호출 → interrupt 응답이면 “날짜/시간을 알려주세요” + 입력창 표시 → 사용자 입력 시 `POST /api/scheduler/resume` 호출.

### 6.3 공통

- [ ] **thread_id**: 한 번의 “일정 추출 세션”을 식별. Next.js에서 생성해 extract/resume 모두 같은 값을 넘기면 됩니다 (UUID 권장).
- [ ] **에러 처리**: 에이전트 서버 타임아웃, 5xx 시 사용자에게 재시도/안내 메시지.
- [ ] **CORS**: FastAPI에서 Next.js 도메인 허용 (개발 시 localhost).

---

## 7. 요약

| 구분 | 내용 |
|------|------|
| **아키텍처** | Next.js(BFF + UI) + FastAPI(LangGraph 에이전트) 마이크로서비스 |
| **데이터 흐름** | 업로드 → Next.js API → 에이전트(Plan/Execute/Refine) → 정제 JSON 반환 또는 interrupt → 완료 시 Next.js가 DB 저장 → 스케줄러 화면은 DB 조회 |
| **DB** | PostgreSQL `schedules` 테이블에 에이전트 추출 필드(날짜, 시간, 일정명, 준비물, memo, todo_list) 저장 |
| **interrupt 처리** | 에이전트가 질문 문자열 반환 → 프론트에서 사용자에게 표시 → 사용자 답변으로 resume API 호출 → 완료 후 DB 저장 |

이 전략에 따라 RHYMIA-scheduler에 FastAPI 서버를 추가하고, Next.js에 API Route와 스케줄러/업로드 UI를 연결하면 **에이전트 기반 지능형 스케줄러**로 자연스럽게 확장할 수 있습니다.

---

## 8. 구현 예시 코드

### 8.1 에이전트 서버 실행 (RHYMIA-scheduler)

```bash
cd RHYMIA-scheduler
pip install -r requirements.txt
# OPENAI_API_KEY 환경 변수 설정 후
python server.py
# 또는: uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

- `POST http://localhost:8000/scheduler/extract`: JSON body `{ "user_text": "3월 20일 수학 여행", "thread_id": "optional-uuid" }` 또는 `{ "image_base64": "data:image/png;base64,..." }`
- `POST http://localhost:8000/scheduler/resume`: JSON body `{ "thread_id": "...", "user_reply": "3월 15일 오후 2시" }`

서버 코드: **`RHYMIA-scheduler/server.py`** (이미 작성됨)

### 8.2 Next.js API Route 예시 (BFF)

Next.js 앱에서 **`app/api/scheduler/extract/route.ts`** 로 다음처럼 BFF를 두고, 에이전트 서버를 호출한 뒤 완료 시 DB에 저장할 수 있습니다.

```typescript
// app/api/scheduler/extract/route.ts (Next.js App Router)
import { NextRequest, NextResponse } from 'next/server';

const SCHEDULER_AGENT_URL = process.env.SCHEDULER_AGENT_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const userText = (formData.get('user_text') as string) || '';
    const file = formData.get('image') as File | null;
    const threadId = (formData.get('thread_id') as string) || undefined;

    let imageBase64: string | undefined;
    if (file && file.size > 0) {
      const buf = await file.arrayBuffer();
      const base64 = Buffer.from(buf).toString('base64');
      const mime = file.type || 'image/jpeg';
      imageBase64 = `data:${mime};base64,${base64}`;
    }

    const body: Record<string, string> = {};
    if (userText) body.user_text = userText;
    if (imageBase64) body.image_base64 = imageBase64;
    if (threadId) body.thread_id = threadId;

    const res = await fetch(`${SCHEDULER_AGENT_URL}/scheduler/extract`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();

    if (!res.ok) {
      return NextResponse.json({ error: data.detail || '에이전트 서버 오류' }, { status: res.status });
    }

    // interrupt면 그대로 반환 (클라이언트에서 날짜/시간 입력 UI 표시 후 resume 호출)
    if (data.interrupt) {
      return NextResponse.json({ interrupt: true, thread_id: data.thread_id, message: data.message });
    }

    // 완료: 여기서 DB에 저장한 뒤 클라이언트에 반환
    // await saveScheduleToDb(data.extracted, userId);
    return NextResponse.json({
      interrupt: false,
      thread_id: data.thread_id,
      extracted: data.extracted,
      saved_path: data.saved_path,
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
```

**Resume 전용 Route** (`app/api/scheduler/resume/route.ts`):

```typescript
// app/api/scheduler/resume/route.ts
import { NextRequest, NextResponse } from 'next/server';

const SCHEDULER_AGENT_URL = process.env.SCHEDULER_AGENT_URL || 'http://localhost:8000';

export async function POST(req: NextRequest) {
  try {
    const { thread_id, user_reply } = await req.json();
    if (!thread_id || !user_reply) {
      return NextResponse.json({ error: 'thread_id, user_reply 필요' }, { status: 400 });
    }
    const res = await fetch(`${SCHEDULER_AGENT_URL}/scheduler/resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id, user_reply }),
    });
    const data = await res.json();
    if (!res.ok) {
      return NextResponse.json({ error: data.detail || '에이전트 서버 오류' }, { status: res.status });
    }
    if (data.interrupt) {
      return NextResponse.json({ interrupt: true, thread_id: data.thread_id, message: data.message });
    }
    // 완료 시 DB 저장 후 반환
    // await saveScheduleToDb(data.extracted, userId);
    return NextResponse.json({
      interrupt: false,
      extracted: data.extracted,
      saved_path: data.saved_path,
    });
  } catch (e) {
    return NextResponse.json({ error: String(e) }, { status: 500 });
  }
}
```

- 환경 변수: `SCHEDULER_AGENT_URL=http://localhost:8000` (에이전트 서버 주소)
- DB 저장 함수 `saveScheduleToDb(extracted, userId)`는 위 4장 스키마에 맞게 `schedules` 테이블에 insert하면 됩니다.
