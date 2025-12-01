# NewsBot

간단한 뉴스 수집/요약/공유(슬랙) 데모 애플리케이션입니다. 초기 목표는 폴더 구조와 모듈 간 연결이 정상 동작하는 "Hello World" 수준의 엔드투엔드 흐름을 확인하는 것입니다.

## 목차

1. 기술 스택
2. 폴더 구조
3. 빠른 시작
4. 환경 변수(.env)
5. 제공 라우트(데모)
6. 개발 메모
7. 참고 문서
8. 요구사항 요약 (1단계 MVP)
9. 참고 링크 (Confluence)
10. 설계 기준 요약 (초안)
11. 변경 이력

## 1. 기술 스택

- Python 3.9+
- Flask
- python-dotenv

## 2. 폴더 구조

```
./
  app.py
  modules/
    __init__.py
    crawler.py
    gemini.py
    slack.py
  templates/
    index.html
  static/
    css/
  .env.sample
  .gitignore
  requirements.txt
  README.md
  venv/
```

## 3. 빠른 시작

### macOS / Linux 환경

아래 순서대로 실행합니다.

```bash
# 1) 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 2) 의존성 설치
pip install -r requirements.txt

# 3) 환경변수 파일 생성 (샘플 복사)
cp .env.sample .env

# 4) 서버 실행 (포트 5001)
flask --app app run --host=0.0.0.0 --port 5001
# 참고: 백그라운드 실행/서버 종료/venv 비활성화는 아래 '개발 메모 > 개발 명령어 치트시트' 참조
```

### Windows 환경

**PowerShell 사용 시:**

```powershell
# 1) 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2) 의존성 설치
pip install -r requirements.txt

# 3) 환경변수 파일 생성 (샘플 복사)
Copy-Item .env.sample .env

# 4) 서버 실행 (포트 5001)
flask --app app run --host=0.0.0.0 --port 5001
```

**명령 프롬프트(CMD) 사용 시:**

```cmd
# 1) 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate.bat

# 2) 의존성 설치
pip install -r requirements.txt

# 3) 환경변수 파일 생성 (샘플 복사)
copy .env.sample .env

# 4) 서버 실행 (포트 5001)
flask --app app run --host=0.0.0.0 --port 5001
```

**Windows 주의사항:**

- PowerShell에서 스크립트 실행이 차단된 경우:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- Python이 설치되어 있지 않은 경우: [Python 공식 사이트](https://www.python.org/downloads/)에서 Python 3.9 이상을 다운로드하여 설치하세요.
- `python` 명령어가 인식되지 않는 경우: 설치 시 "Add Python to PATH" 옵션을 선택했는지 확인하거나, 전체 경로를 사용하세요 (예: `C:\Python39\python.exe`).

브라우저에서 `http://127.0.0.1:5001` 접속 후 초기 페이지가 보이면 성공입니다.

## 4. 환경 변수(.env)

`.env.sample`을 참고하여 `.env`를 생성합니다.

| 키                        | 설명                                                  |
| ------------------------- | ----------------------------------------------------- | ----- |
| `GEMINI_API_KEY`          | 요약용 외부 모델(예: Gemini) 호출 시 사용하는 API 키  |
| `SLACK_BOT_TOKEN`         | 슬랙 봇 토큰                                          |
| `SLACK_CHANNEL_ID`        | 메시지를 보낼 기본 채널 ID                            |
| `REALDATA_ENABLED`        | 실데이터(네이버 뉴스 API) 사용 여부(true/false)       |
| `NAVER_API_CLIENT_ID`     | 네이버 검색 API 클라이언트 ID                         |
| `NAVER_API_CLIENT_SECRET` | 네이버 검색 API 클라이언트 시크릿                     |
| `NAVER_QUERY_KEYWORDS`    | 쉼표 구분 키워드 목록(예: 현대백화점,식권대장,vendys) |
| `NAVER_MAX_ARTICLES`      | 최대 수집 기사 수(카테고리 합)                        |
| `NAVER_TIMEOUT_MS`        | 네이버 API 호출 타임아웃(ms)                          |
| `NAVER_SORT`              | 정렬(sim                                              | date) |
| `NAVER_DELAY_MS`          | 키워드 호출 간 대기(ms)                               |

초기 실행 단계에서는 실제 키가 없어도 서버 기동과 라우트 연결 확인에는 문제가 없습니다.

## 5. 제공 라우트(데모)

- `GET /` 템플릿 렌더링 테스트
- `POST /api/collect` 뉴스 수집 더미 응답
- `POST /api/summarize` 기사 요약 더미 응답
- `POST /api/send-slack` 슬랙 발송 더미 응답

예시 요청:

```bash
curl -X POST http://127.0.0.1:5001/api/collect
curl -X POST http://127.0.0.1:5001/api/summarize
curl -X POST http://127.0.0.1:5001/api/send-slack
```

## 6. 개발 메모

- 서버 로그: 백그라운드 실행 시 `.flask.log`를 확인해 문제를 진단할 수 있습니다.
- 포트 충돌 시 `--port` 값을 변경해 실행합니다.

### 개발 명령어 치트시트

#### macOS / Linux

```bash
# 가상환경 생성/활성화/비활성화
python3 -m venv venv
source venv/bin/activate
deactivate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (포그라운드/백그라운드)
flask --app app run --host=0.0.0.0 --port 5001
flask --app app run --host=0.0.0.0 --port 5001 > .flask.log 2>&1 & echo $! > .flask.pid

# 서버 종료 (백그라운드)
if [ -f .flask.pid ]; then kill $(cat .flask.pid); fi

# 서버 재기동 (백그라운드)
if [ -f .flask.pid ]; then kill $(cat .flask.pid); fi \
  && flask --app app run --host=0.0.0.0 --port 5001 > .flask.log 2>&1 & echo $! > .flask.pid
```

#### Windows (PowerShell)

```powershell
# 가상환경 생성/활성화/비활성화
python -m venv venv
.\venv\Scripts\Activate.ps1
deactivate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (포그라운드)
flask --app app run --host=0.0.0.0 --port 5001

# 서버 실행 (백그라운드 - 새 PowerShell 창에서)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\venv\Scripts\Activate.ps1; flask --app app run --host=0.0.0.0 --port 5001"

# 서버 종료 (포트 5001 사용 프로세스 종료)
Get-Process | Where-Object {$_.Path -like "*python*"} | Stop-Process -Force
# 또는 특정 포트 사용 프로세스 종료
netstat -ano | findstr :5001
taskkill /PID <PID번호> /F
```

#### Windows (CMD)

```cmd
# 가상환경 생성/활성화/비활성화
python -m venv venv
venv\Scripts\activate.bat
deactivate

# 의존성 설치
pip install -r requirements.txt

# 서버 실행 (포그라운드)
flask --app app run --host=0.0.0.0 --port 5001

# 서버 실행 (백그라운드 - 새 CMD 창에서)
start cmd /k "cd /d %CD% && venv\Scripts\activate.bat && flask --app app run --host=0.0.0.0 --port 5001"

# 서버 종료 (포트 5001 사용 프로세스 종료)
netstat -ano | findstr :5001
taskkill /PID <PID번호> /F
```

## 7. 참고 문서

- 프로젝트 설정 및 실행 가이드: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4318003228`

---

## 8. 요구사항 요약 (1단계 MVP)

- **목표**: 수동 뉴스 클리핑 시간을 1시간 30분 → 30분 이내로 단축
- **주요 사용자**: 세일즈 팀원(정보 소비), 뉴스 담당자(관리/발행)
- **소스**: 네이버 뉴스 (고정 키워드 기반 수집)
- **발송**: `#new_biz` 채널, 1일 1회, 현재 포맷 유지(이모지/볼드 등)
- **운영 목표**: 매일 9시~10시 사이 발행 완료

### 8.1 카테고리 및 키워드

- **그룹사 뉴스**: 현대이지웰, 현대백화점(그룹), 현대그린푸드, 식권대장, 복지대장, vendys, 조정호, 현대벤디스
- **업계 뉴스**: 모바일/전자 식권, 식권 앱/플랫폼, 식대 정산/지원, 기업 복지/포인트/복지몰, 배달 앱/플랫폼, 이커머스, 간편식/밀키트, 푸드테크
- **참고 뉴스**: MRO, 기업 문화, 사무실/업무 공간, 워크플레이스, 오피스
- **읽을 거리**: 위 키워드 외 주요 IT/경제/문화 뉴스(키워드 없음)

### 8.2 사용자 플로우 (1단계)

1. [수동] 검토 페이지에서 `뉴스 수집` 클릭 → 키워드 기반 수집 및 자동 분류/1차 중복 제거
2. [수동] 목록 검토 및 불필요 기사 제거, 발행 대상 확정
3. [수동] `뉴스 요약하기` 클릭 → Gemini API 3~5줄 요약 생성
4. [수동] `슬랙으로 발송` 클릭 → `#new_biz`로 즉시 발송 (1일 1회)

### 8.3 운영 정책

- 발송 전 담당자 검토/승인 (100% 자동 발송은 1단계 범위 외)
- 중복/광고성 기사는 1차 자동 필터 + 담당자 최종 확인

### 8.4 향후 고려사항 (2단계)

- 키워드/소스/발송 시간 관리 UI 제공
- 예약 수집/발송(스케줄러)
- 이메일 뉴스레터 확장 검토

---

## 9. 참고 링크 (Confluence)

- 요구사항 분석 질문 목록: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4313645058`
- 카테고리별 뉴스 검색 키워드 정의: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4320657410`
- 제품 요구사항 정의서(PRD): `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4315283476/PRD`
- 검토 페이지 와이어프레임: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4315185158`

### 9.1 설계 문서 (추가 링크)

- UI/UX: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4318855194/UI+UX`
- 설계 문서 A: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4318298121`
- 설계 문서 B: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4319674386`
- 설계 문서 C: `https://vendysdev.atlassian.net/wiki/spaces/PROD/pages/4320952321`

---

## 10. 설계 기준 요약 (초안)

해당 섹션은 Confluence 설계 문서를 바탕으로 개발·디자인 공통 기준을 요약해 유지합니다. 현재 일부 설계 문서는 접근 권한/세션 이슈로 본문 동기화가 보류되어 있으며, 아래 링크를 우선 참조합니다. 권한 복구 시 상세 규칙을 본 섹션에 반영합니다.

### 10.1 UI/UX 가이드 (자세한 내용은 9장 링크 참조)

- 참고: 9.1 UI/UX 설계 문서 링크
- 반영 위치: 컴포넌트 스타일 토큰(색/타이포/간격), 상태/피드백 패턴, 접근성(키보드 포커스, 대비), 반응형 기준

### 10.2 검토 페이지 레이아웃/플로우 (자세한 내용은 9장 링크 참조)

- 참고: 9장 '검토 페이지 와이어프레임'
- 반영 위치: 카테고리 필터, 기사 카드(제목 링크/출처/날짜/요약), 액션 버튼(뉴스 수집/요약/슬랙 발송), 삭제/선택 동작

### 10.3 도메인 카테고리·키워드 매핑 (자세한 내용은 9장 링크 참조)

- 참고: 9장 '카테고리별 뉴스 검색 키워드 정의'
- 반영 위치: 그룹사/업계/참고/읽을거리 카테고리 정의와 키워드 매핑 규칙(중복/광고성 1차 필터 기준 포함)

### 10.4 발송 정책·메시지 포맷 (자세한 내용은 9장 링크 참조)

- 참고: 9장 '제품 요구사항 정의서(PRD)'
- 반영 위치: 발송 주기(1일 1회), 시간대(9~10시 목표), 채널(`#new_biz`), 포맷(이모지/헤드라인 볼드 유지)

## 11. 변경 이력

- 2025-10-16: 목차/치트시트 추가, 요구/설계 문서 인용 및 설계 기준 요약 섹션 정리

---

## 12. 운영 체크리스트 (일일)

- [ ] 09:00 수집 실행(`/review` → "뉴스 수집")
- [ ] 자동 분류/중복 제거 결과 확인
- [ ] 불필요 기사 삭제 및 발송 대상 선택
- [ ] 필요한 기사 요약 실행("뉴스 요약하기")
- [ ] 슬랙 발송 전 미리보기(프리뷰 메시지 확인)
- [ ] `#new_biz` 채널 발송 완료 확인(9~10시 목표)

## 13. 2단계 백로그 (요약)

- [ ] 예약 수집/발송(스케줄러)
- [ ] 키워드/소스/발송 시간 관리 UI
- [ ] 슬랙 실연동(chat.postMessage) 및 에러 처리/재시도
- [ ] 이메일 뉴스레터 확장
- [ ] DB 도입(SQLite→향후 확장) 및 마이그레이션 레이어

---

## 14. 슬랙 실발송 전환 가이드

1. 환경 변수 설정

```env
SLACK_BOT_TOKEN="xoxb-..."
SLACK_CHANNEL_ID="new_biz"
```

2. 프리뷰에서 실발송으로 전환

- 현재는 토큰/채널 미설정 시 프리뷰 모드로 메시지를 반환합니다.
- 토큰/채널이 설정되면 `modules/slack.py` 내 TODO 위치에 `chat.postMessage` 연동을 추가합니다(표준 라이브러리 `urllib` 권장).
  - 요청 실패 시 재시도(지수 백오프), 429/5xx 처리
  - 성공/실패 로그 남기기

3. 운영 권장 사항

- 발송 전 `/review`에서 최종 선택/요약 확인 후 발송
- 운영 키는 `.env`(로컬) 또는 안전한 비밀 관리 스토어(CI/CD)에서 주입
