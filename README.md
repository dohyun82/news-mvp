# vendys-ai-automation-platform

사내 AI 자동화 기능을 제공하는 플랫폼입니다. 뉴스 클리핑 기능을 모듈화된 구조로 제공합니다.

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
  app.py                          # Flask 앱 초기화 및 Blueprint 등록
  apps/                           # 기능별 앱 모듈
    news/                         # 뉴스 클리핑 앱
      routes.py
      services.py
      models.py                   # Article + 파일 영속 InMemoryStore
      templates/
  core/                           # 공통 기반
    config.py                     # 설정(Slack/OpenAI/ArticleFetch/RealData)
    common.py                     # 로깅·에러 핸들러
  shared/                         # 재사용 모듈
    ai/                           # AI 클라이언트
      openai_client.py
    integrations/                 # 외부 연동
      slack.py
    news/                         # 기사 본문 추출
      article_content_extractor.py
  modules/                        # 레거시 (점진 정리 중)
    crawler.py
    curation.py
    keyword_store.py
  templates/                      # 공통 템플릿
    base.html
    index.html
    review.html
    settings.html
  static/
    css/
  data/
    keywords.json                 # 키워드/카테고리 설정
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

| 키                        | 설명                                                 |
| ------------------------- | ---------------------------------------------------- | ----- |
| `OPENAI_API_KEY`          | 요약용 외부 모델(예: OpenAI) 호출 시 사용하는 API 키 |
| `SLACK_BOT_TOKEN`         | 슬랙 봇 토큰                                         |
| `SLACK_CHANNEL_ID`        | 메시지를 보낼 기본 채널 ID                           |
| `REALDATA_ENABLED`        | 실데이터(네이버 뉴스 API) 사용 여부(true/false)      |
| `NAVER_API_CLIENT_ID`     | 네이버 검색 API 클라이언트 ID                        |
| `NAVER_API_CLIENT_SECRET` | 네이버 검색 API 클라이언트 시크릿                    |
| `NAVER_TIMEOUT_MS`        | 네이버 API 호출 타임아웃(ms)                         |
| `NAVER_SORT`              | 정렬(sim                                             | date) |
| `NAVER_DELAY_MS`          | 키워드 호출 간 대기(ms)                              |

초기 실행 단계에서는 실제 키가 없어도 서버 기동과 라우트 연결 확인에는 문제가 없습니다.

## 5. 제공 라우트

### 뉴스 클리핑 (`/news/*`)

- `GET /news/review` 뉴스 클리핑 검토 페이지
- `GET /news/settings` 뉴스 클리핑 설정 페이지
- `POST /news/api/collect` 뉴스 수집
- `POST /news/api/summarize` 기사 요약
- `GET /news/api/clipboard` 그룹웨어 게시판 복붙용 정리 텍스트(plain/html)
- `GET /news/api/review/list` 뉴스 목록 조회
- `POST /news/api/review/select` 뉴스 선택/해제
- `POST /news/api/review/category` 뉴스 카테고리 변경
- `POST /news/api/review/delete` 뉴스 삭제
- `GET /news/api/settings/get` 설정 조회
- `POST /news/api/settings/save` 설정 저장

### 하위 호환성

기존 라우트(`/api/*`, `/review`, `/settings`)는 새로운 Blueprint 경로로 리다이렉트됩니다.

예시 요청:

```bash
curl -X POST http://127.0.0.1:5001/news/api/collect
curl -X POST http://127.0.0.1:5001/news/api/summarize
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
3. [수동] `뉴스 요약하기` 클릭 → OpenAI API 3~5줄 요약 생성
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
- 반영 위치: 카테고리 필터, 기사 카드(제목 링크/출처/날짜/요약), 액션 버튼(뉴스 수집/요약/복사하기), 삭제/선택 동작

### 10.3 도메인 카테고리·키워드 매핑 (자세한 내용은 9장 링크 참조)

- 참고: 9장 '카테고리별 뉴스 검색 키워드 정의'
- 반영 위치: 그룹사 / 유통·F&B·급식 / 플랫폼·테크 / 경쟁사·복지·HR 트렌드 / 시장·소비 트렌드 / 읽을거리 카테고리. 분류는 검토 화면에서 수동 지정(중복/광고성은 1차 자동 필터)

### 10.4 게시 정책·포맷 (자세한 내용은 9장 링크 참조)

- 참고: 9장 '제품 요구사항 정의서(PRD)'
- 반영 위치: 게시 주기(1일 1회), 시간대(9~10시 목표), 그룹웨어 게시판 복붙, 포맷(카테고리별 이모지 + 제목/링크/요약)

## 11. 변경 이력

- 2025-10-16: 목차/치트시트 추가, 요구/설계 문서 인용 및 설계 기준 요약 섹션 정리
- 2026-06-18: 카테고리 5개 개편·수동 분류 전환, 슬랙 발송 제거 및 그룹웨어 복붙으로 대체

---

## 12. 운영 체크리스트 (일일)

- [ ] 09:00 수집 실행(`/review` → "뉴스 수집")
- [ ] 자동 분류/중복 제거 결과 확인
- [ ] 불필요 기사 삭제 및 발송 대상 선택
- [ ] 필요한 기사 요약 실행("뉴스 요약하기")
- [ ] "복사하기"로 정리 내용 확인(미리보기)
- [ ] 그룹웨어 게시판 붙여넣기·게시 완료 확인(9~10시 목표)

## 13. 2단계 백로그 (요약)

- [ ] 예약 수집/발송(스케줄러)
- [ ] 키워드/소스/발송 시간 관리 UI
- [ ] 이메일 뉴스레터 확장
- [ ] DB 도입(SQLite→향후 확장) 및 마이그레이션 레이어

---

## 14. 그룹웨어 게시판 복붙 사용

1. `/news/review`에서 뉴스를 수집하고, 6개 카테고리(그룹사 / 유통·F&B·급식 / 플랫폼·테크 / 경쟁사·복지·HR 트렌드 / 시장·소비 트렌드 / 읽을거리)로 드래그해 분류한 뒤 요약합니다.
2. **"복사하기"** 버튼을 누르면 카테고리별로 정리된 내용이 클립보드에 복사됩니다(`GET /news/api/clipboard`가 `plain`/`html` 제공).
3. 그룹웨어 게시판 작성 화면에 붙여넣습니다.

- 브라우저 클립보드 API는 HTTPS 또는 localhost에서만 동작하므로, 사내망 HTTP 접속 시 화면 하단 미리보기에서 직접 복사(Ctrl/Cmd+C)하세요.
- 카테고리 정의·이모지는 `core/categories.py` 한 곳에서 관리합니다.
