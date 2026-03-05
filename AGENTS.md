# AGENTS.md

이 문서는 AI 에이전트가 이 저장소에서 **안전하고 일관되게 작업**하기 위한 지침이다.
사람 개발자를 위한 상세 문서는 `@README.md`, `@DEVELOPMENT_GUIDE.md`, `@USER_MANUAL.md`를 참고한다.

## 우선순위
- 사용자 요청이 최우선이며, 그 다음으로 가장 가까운 경로의 AGENTS.md 지침이 적용된다.
- 하위 디렉터리에 AGENTS.md가 추가되면 해당 디렉터리의 작업은 그 지침을 따른다.

## 빠른 시작
- 가상환경 생성/활성화:
  - `python3 -m venv venv`
  - `source venv/bin/activate`
- 의존성 설치: `pip install -r requirements.txt`
- 로컬 환경파일 생성: `cp .env.sample .env`
- 앱 실행: `flask --app app run --host=0.0.0.0 --port 5001`
- 테스트 실행: `python -m unittest discover -s tests`

## 프로젝트 구조
- `app.py`: Flask 엔트리 포인트, Blueprint 등록.
- `apps/`: 기능 모듈(`news/`, `logs/`) + 각 모듈의 `routes.py`, `services.py`, 템플릿.
- `core/`: 공통 설정, 요청/응답 헬퍼.
- `shared/`: 재사용 통합(예: AI 클라이언트, Slack/Datadog, 스토리지).
- `modules/`: 마이그레이션 중인 레거시(크롤러, 키워드 스토어 등).
- `templates/`, `static/`: 공유 Jinja2 레이아웃/에셋.
- `data/keywords.json`: 키워드/카테고리 매핑.
- `tests/`: 단위 테스트(`test_*.py`).

## 작업 원칙 (Do / Don’t)
- Do: 변경 범위를 작게 유지하고 기존 구조/패턴을 우선 활용한다.
- Do: Flask 라우트는 Blueprint 단위로 묶는다.
- Do: 외부 연동(Naver/Slack/OpenAI)은 테스트에서 반드시 mock 처리한다.
- Do: `modules/` 레거시 수정 시 동일 기능이 `apps/`로 이동 예정인지 확인한다.
- Don’t: 명시 요청 없이 새 의존성 추가/삭제 또는 대규모 리팩터링을 진행하지 않는다.
- Don’t: 실제 키/토큰을 커밋하지 않는다.
- Don’t: `data/keywords.json` 또는 `.env.sample` 변경을 누락한 채 PR을 올리지 않는다.

## 코드 스타일
- Python 3.9+, 4-space indentation.
- 함수/모듈은 `snake_case`.
- 템플릿은 각 기능 모듈의 `templates/`와 루트 `templates/`에 위치.
- 포매터/린터 강제 없음: PEP 8 준수, 가독성 중심으로 변경.

## 테스트
- 프레임워크: `unittest`.
- 파일명 규칙: `tests/test_*.py`.
- 필요 시 파일 단위 실행: `python -m unittest tests/test_x.py` (실제 파일명으로 변경).
- 테스트는 외부 네트워크를 호출하지 않도록 mock을 사용한다.

## 보안 & 설정
- 로컬에 `.env` 사용, 실제 자격 증명은 커밋 금지.
- 필수 키: `OPENAI_API_KEY`, `SLACK_BOT_TOKEN`, `NAVER_API_CLIENT_ID` (Datadog 토큰은 필요 시).
- 환경 변수 추가/변경 시 `.env.sample`도 함께 업데이트한다.

## 커밋 & PR
- 커밋 메시지: `feat:`, `refactor:`, `docs:`, `bugfix:`, `chore:` 형식(짧고 명확하게).
- PR 포함 사항: 변경 요약, 테스트 방법, UI 변경 시 스크린샷/GIF.
- `data/keywords.json` 또는 `.env.sample` 변경은 PR 설명에 명시.

## 작업 후 체크리스트
- 변경 관련 테스트를 실행하고 실패가 없도록 정리한다.
- 환경 변수 추가/변경이 있다면 `.env.sample`을 업데이트한다.
