# NewsBot 개발 가이드 (주니어 개발자용)

> **목적**: Python과 Flask에 대한 개념이 부족한 주니어 개발자가 이 프로젝트를 이해하고, 코딩하면서 개념도 함께 학습할 수 있도록 돕는 가이드입니다.

## 📚 목차

1. [Python & Flask 기본 개념](#1-python--flask-기본-개념)
2. [프로젝트 구조 이해하기](#2-프로젝트-구조-이해하기)
3. [코드 수정/추가/삭제 가이드라인](#3-코드-수정추가삭제-가이드라인)
4. [모듈별 상세 설명](#4-모듈별-상세-설명)
5. [실전 예제: 기능 추가하기](#5-실전-예제-기능-추가하기)
6. [디버깅 팁](#6-디버깅-팁)
7. [자주 묻는 질문 (FAQ)](#7-자주-묻는-질문-faq)

---

## 1. Python & Flask 기본 개념

### 1.1 Python 기본 개념

#### 모듈 (Module)

- **개념**: Python 파일 하나가 하나의 모듈입니다. 다른 파일에서 `import`로 가져와 사용할 수 있습니다.
- **예시**: `modules/crawler.py`는 `crawler`라는 이름의 모듈입니다.
- **사용법**:
  ```python
  # 다른 파일에서 사용할 때
  from modules import crawler  # modules 폴더의 crawler 모듈을 가져옴
  crawler.crawl_naver_news([])  # crawler 모듈의 함수 호출
  ```

#### 패키지 (Package)

- **개념**: 여러 모듈을 묶어놓은 폴더입니다. `__init__.py` 파일이 있으면 Python이 그 폴더를 패키지로 인식합니다.
- **예시**: `modules/` 폴더는 패키지입니다. `modules/__init__.py` 파일이 있어서 가능합니다.
- **사용법**:
  ```python
  from modules import crawler, gemini, slack  # 패키지에서 여러 모듈 가져오기
  ```

#### 함수 (Function)

- **개념**: 특정 작업을 수행하는 코드 블록입니다. `def` 키워드로 정의합니다.
- **예시**:
  ```python
  def collect_news():
      articles = crawler.crawl_naver_news([])
      return articles
  ```
- **매개변수 (Parameter)**: 함수에 전달하는 값

  ```python
  def greet(name):  # name이 매개변수
      return f"Hello, {name}"

  greet("철수")  # "철수"가 인자(argument)
  ```

#### 클래스 (Class)

- **개념**: 데이터와 함수를 묶어놓은 설계도입니다. 객체 지향 프로그래밍의 핵심입니다.
- **예시**:
  ```python
  class InMemoryStore:
      def __init__(self):  # 생성자: 객체가 만들어질 때 실행
          self._articles = []  # 인스턴스 변수

      def set_articles(self, articles):  # 메서드: 클래스 내부 함수
          self._articles = articles
  ```
- **인스턴스 (Instance)**: 클래스로 만든 실제 객체
  ```python
  store = InMemoryStore()  # store는 InMemoryStore의 인스턴스
  store.set_articles([])   # 인스턴스의 메서드 호출
  ```

#### 데코레이터 (Decorator)

- **개념**: 함수나 클래스를 꾸며주는 기능입니다. `@` 기호로 사용합니다.
- **예시**:
  ```python
  @app.route('/api/collect', methods=['POST'])  # Flask 데코레이터
  def collect_news():
      return jsonify({"count": 10})
  ```
- **동작 원리**: `@app.route()` 데코레이터는 `collect_news` 함수를 Flask에 등록합니다.
  - Flask가 `/api/collect` 경로로 POST 요청이 오면 `collect_news()` 함수를 실행합니다.

### 1.2 Flask 기본 개념

#### Flask란?

- **개념**: Python으로 웹 애플리케이션을 만드는 프레임워크입니다.
- **역할**: HTTP 요청을 받아서 처리하고, 응답을 반환합니다.

#### Flask 앱 생성

```python
from flask import Flask

app = Flask(__name__)  # Flask 애플리케이션 객체 생성
# __name__은 현재 파일의 이름입니다 (여기서는 "app")
```

#### 라우트 (Route)

- **개념**: URL 경로와 함수를 연결하는 것입니다.
- **예시**:

  ```python
  @app.route('/')  # http://localhost:5001/ 경로
  def index():
      return render_template('index.html')

  @app.route('/api/collect', methods=['POST'])  # POST 메서드만 허용
  def collect_news():
      return jsonify({"count": 10})
  ```

- **HTTP 메서드**:
  - `GET`: 데이터 조회 (기본값)
  - `POST`: 데이터 생성/전송
  - `PUT`: 데이터 수정
  - `DELETE`: 데이터 삭제

#### 요청 처리 (Request)

- **개념**: 클라이언트(브라우저)가 보낸 데이터를 받는 것입니다.
- **예시**:

  ```python
  from flask import request

  @app.route('/api/summarize', methods=['POST'])
  def summarize_news():
      data = request.get_json()  # JSON 데이터 받기
      url = data.get("url")      # "url" 키의 값 가져오기
      return jsonify({"url": url})
  ```

#### 응답 반환 (Response)

- **JSON 응답**:

  ```python
  from flask import jsonify

  return jsonify({"success": True, "message": "완료"})
  ```

- **HTML 템플릿 렌더링**:

  ```python
  from flask import render_template

  return render_template('index.html')  # templates/index.html 파일 렌더링
  ```

#### Flask 앱 실행

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5001)
```

- `host='0.0.0.0'`: 모든 네트워크 인터페이스에서 접속 허용
- `debug=True`: 개발 모드 (코드 변경 시 자동 재시작, 에러 상세 표시)
- `port=5001`: 5001 포트에서 실행

---

## 2. 프로젝트 구조 이해하기

```
news-mvp/
├── app.py                 # Flask 앱의 진입점 (메인 파일)
├── modules/               # 비즈니스 로직 모듈들
│   ├── __init__.py       # 패키지 초기화 파일
│   ├── common.py         # 공통 유틸리티 (로깅, 에러 처리)
│   ├── config.py         # 설정 관리 (환경 변수, 상수)
│   ├── crawler.py        # 뉴스 수집 로직
│   ├── curation.py       # 뉴스 큐레이션 로직
│   ├── gemini.py         # Gemini API 연동 (요약 생성)
│   ├── slack.py          # Slack API 연동 (메시지 발송)
│   └── store.py          # 인메모리 데이터 저장소
├── templates/            # HTML 템플릿 파일들
│   ├── index.html        # 메인 페이지
│   └── review.html       # 검토 페이지
├── static/               # 정적 파일 (CSS, JS, 이미지)
│   └── css/
├── tests/                # 테스트 파일들
│   ├── test_curation.py
│   ├── test_integration_realdata.py
│   └── test_slack.py
├── requirements.txt      # Python 패키지 의존성 목록
└── README.md             # 프로젝트 설명서
```

### 2.1 파일 역할 설명

#### `app.py` - 애플리케이션 진입점

- **역할**: Flask 앱을 생성하고, 모든 라우트를 정의합니다.
- **핵심 코드**:

  ```python
  app = Flask(__name__)  # Flask 앱 생성

  @app.route('/api/collect', methods=['POST'])
  def collect_news():
      # 뉴스 수집 로직
      pass
  ```

#### `modules/` - 비즈니스 로직

- **역할**: 실제 기능을 구현하는 코드들이 모여있습니다.
- **설계 원칙**: 각 모듈은 하나의 책임만 가집니다 (Single Responsibility Principle)
  - `crawler.py`: 뉴스 수집만 담당
  - `gemini.py`: 요약 생성만 담당
  - `slack.py`: Slack 발송만 담당

#### `templates/` - HTML 템플릿

- **역할**: 사용자에게 보여줄 HTML 페이지입니다.
- **Flask 템플릿 엔진**: Jinja2를 사용합니다.
  ```html
  <!-- templates/index.html -->
  <h1>{{ title }}</h1>
  <!-- Python 변수를 HTML에 삽입 -->
  ```

---

## 3. 코드 수정/추가/삭제 가이드라인

### 3.1 코드 수정 시 설명 규칙

코드를 수정할 때는 **반드시** 다음 정보를 포함해야 합니다:

1. **수정 전 코드**: 원래 코드가 무엇이었는지
2. **수정 후 코드**: 어떻게 바뀌었는지
3. **수정 이유**: 왜 이렇게 바꿨는지
4. **관련 개념**: 이 수정과 관련된 Python/Flask 개념 설명

#### 예시: 함수 수정

**수정 전**:

```python
def get_article_by_url(self, url: str):
    for a in self._articles:
        if a.url == url:
            return a
    return None
```

**수정 후**:

```python
def get_article_by_url(self, url: str) -> Optional[Article]:
    """URL로 기사를 찾아 반환합니다. 없으면 None을 반환합니다.

    Args:
        url: 찾을 기사의 URL

    Returns:
        Article 객체 또는 None
    """
    for a in self._articles:
        if a.url == url:
            return a
    return None
```

**수정 이유**:

- 반환 타입을 명시적으로 표시 (`-> Optional[Article]`)
- 함수에 docstring 추가로 사용법 명확화
- `Optional`은 "값이 있거나 None일 수 있다"는 의미입니다.

**관련 개념**:

- **타입 힌트 (Type Hint)**: Python 3.5+에서 함수의 매개변수와 반환값의 타입을 명시하는 기능입니다.
  - `Optional[Article]`: `Article` 타입이거나 `None`일 수 있음
  - 코드 가독성과 IDE 자동완성 기능 향상에 도움

### 3.2 코드 추가 시 설명 규칙

새로운 코드를 추가할 때는 다음을 포함해야 합니다:

1. **추가 위치**: 어디에 추가하는지
2. **추가 이유**: 왜 이 코드가 필요한지
3. **동작 원리**: 코드가 어떻게 작동하는지
4. **관련 개념**: 사용된 Python/Flask 개념 설명

#### 예시: 새로운 API 엔드포인트 추가

**추가 위치**: `app.py` 파일의 라우트 섹션

**추가 코드**:

```python
@app.route('/api/articles/<article_id>', methods=['GET'])
def get_article(article_id: str):
    """특정 기사의 상세 정보를 반환합니다.

    Args:
        article_id: 기사 ID (URL 경로에서 추출)

    Returns:
        JSON 형태의 기사 정보
    """
    article = store.get_article_by_id(article_id)
    if not article:
        return jsonify({"error": "Article not found"}), 404
    return jsonify({
        "title": article.title,
        "url": article.url,
        "category": article.category
    })
```

**추가 이유**:

- 프론트엔드에서 특정 기사의 상세 정보를 조회할 수 있도록 하기 위해

**동작 원리**:

1. `@app.route('/api/articles/<article_id>', methods=['GET'])`
   - URL 경로에 변수를 포함: `/api/articles/123` → `article_id = "123"`
2. `store.get_article_by_id(article_id)`
   - 저장소에서 기사 조회
3. `if not article:`
   - 기사가 없으면 404 에러 반환
4. `return jsonify(...)`
   - 기사 정보를 JSON 형태로 반환

**관련 개념**:

- **URL 변수 (Dynamic Route)**: Flask에서 URL 경로에 변수를 포함할 수 있습니다.
  - `<article_id>`: 문자열 변수
  - `<int:article_id>`: 정수 변수로 변환
- **HTTP 상태 코드**:
  - `200`: 성공
  - `404`: 리소스를 찾을 수 없음
  - `500`: 서버 내부 오류

### 3.3 코드 삭제 시 설명 규칙

코드를 삭제할 때는 다음을 포함해야 합니다:

1. **삭제 대상**: 어떤 코드를 삭제하는지
2. **삭제 이유**: 왜 삭제하는지
3. **영향 범위**: 이 삭제가 다른 코드에 미치는 영향
4. **대체 방안**: 삭제된 기능이 필요하다면 어떻게 대체할지

#### 예시: 사용하지 않는 함수 삭제

**삭제 대상**:

```python
def old_format_article(article: dict) -> str:
    """구식 포맷으로 기사를 변환합니다. (더 이상 사용하지 않음)"""
    return f"제목: {article['title']}\nURL: {article['url']}"
```

**삭제 이유**:

- 새로운 포맷 함수로 대체되어 더 이상 사용되지 않음
- 코드 중복 제거 (DRY 원칙)

**영향 범위**:

- 이 함수를 호출하는 코드가 없다면 안전하게 삭제 가능
- 만약 다른 곳에서 사용 중이라면 먼저 그 부분을 수정해야 함

**대체 방안**:

- `format_article()` 함수를 사용 (새로운 포맷)

---

## 4. 모듈별 상세 설명

### 4.1 `modules/common.py` - 공통 유틸리티

#### 목적

모든 API에서 공통으로 사용하는 로깅과 에러 처리를 중앙화합니다.

#### 주요 함수

##### `configure_logging(level: int = logging.INFO)`

- **역할**: 로깅 시스템을 초기화합니다.
- **동작 원리**:
  ```python
  logging.basicConfig(
      level=level,  # 로그 레벨 설정 (INFO, DEBUG, WARNING, ERROR)
      format="%(asctime)s %(levelname)s %(name)s: %(message)s",
  )
  ```
- **사용 예시**:
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("뉴스 수집 시작")  # 로그 출력
  ```

##### `register_http_logging(app)`

- **역할**: 모든 HTTP 요청과 응답을 자동으로 로깅합니다.
- **동작 원리**:
  - `@app.before_request`: 요청이 처리되기 전에 실행되는 함수
  - `@app.after_request`: 요청이 처리된 후에 실행되는 함수
  - `g` 객체: Flask의 컨텍스트 변수 (요청마다 독립적)
- **코드 설명**:

  ```python
  @app.before_request
  def _start_timer():
      g._start_time = time.perf_counter()  # 요청 시작 시간 저장

  @app.after_request
  def _log_response(resp):
      duration_ms = int((time.perf_counter() - g._start_time) * 1000)
      # 요청 처리 시간 계산 및 로그 출력
  ```

##### `register_error_handlers(app)`

- **역할**: 예상치 못한 예외를 잡아서 JSON 형태로 반환합니다.
- **동작 원리**:
  ```python
  @app.errorhandler(Exception)  # 모든 예외를 처리
  def _handle_exception(err):
      logging.exception("Unhandled exception")  # 에러 로그 기록
      return jsonify({"error": {...}}), 500  # JSON 에러 응답
  ```

**관련 개념**:

- **데코레이터 패턴**: 함수를 감싸서 추가 기능을 제공
- **컨텍스트 변수 (`g`)**: 요청마다 독립적인 변수 저장소

### 4.2 `modules/config.py` - 설정 관리

#### 목적

환경 변수와 도메인 상수를 중앙에서 관리합니다.

#### 주요 클래스

##### `@dataclass` 데코레이터

- **개념**: 데이터를 담는 클래스를 간단하게 만드는 기능
- **예시**:
  ```python
  @dataclass(frozen=True)  # frozen=True: 불변 객체 (수정 불가)
  class SlackConfig:
      bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")
      channel_id: str = os.getenv("SLACK_CHANNEL_ID", "")
  ```
- **사용법**:
  ```python
  config = SlackConfig()  # 자동으로 __init__ 생성됨
  print(config.bot_token)  # 환경 변수 값 출력
  ```

##### 환경 변수 로드

- **개념**: `.env` 파일에서 설정값을 읽어옵니다.
- **동작 원리**:

  ```python
  from dotenv import load_dotenv
  load_dotenv()  # .env 파일 읽기

  token = os.getenv("SLACK_BOT_TOKEN", "")  # 환경 변수 읽기 (없으면 "")
  ```

**관련 개념**:

- **환경 변수**: 운영 환경에 따라 달라지는 설정값 (API 키, 서버 주소 등)
- **`.env` 파일**: 환경 변수를 저장하는 파일 (보안상 Git에 커밋하지 않음)

### 4.3 `modules/store.py` - 데이터 저장소

#### 목적

수집한 뉴스 기사를 메모리에 저장하고 관리합니다.

#### 주요 클래스

##### `Article` 데이터 클래스

- **역할**: 뉴스 기사의 정보를 담는 구조체
- **필드 설명**:
  ```python
  @dataclass
  class Article:
      title: str          # 기사 제목
      url: str            # 기사 URL
      category: str       # 카테고리 (그룹사, 업계, 참고, 읽을거리)
      selected: bool = False  # 발송 선택 여부 (기본값: False)
      summary: str = ""   # 요약 내용 (기본값: 빈 문자열)
      description: str = ""  # 네이버 API 제공 요약
      pub_date: str = ""  # 발행일
  ```

##### `InMemoryStore` 클래스

- **역할**: 기사 목록을 메모리에 저장하고 CRUD 작업을 제공
- **주요 메서드**:

  **`set_articles(articles: List[Dict])`**

  - **역할**: 기사 목록을 저장소에 설정
  - **동작 원리**:
    ```python
    def set_articles(self, articles: List[Dict[str, str]]) -> None:
        # 리스트 컴프리헨션으로 Article 객체 리스트 생성
        self._articles = [
            Article(
                title=a.get("title", ""),      # 딕셔너리에서 값 가져오기 (없으면 "")
                url=a.get("url", ""),
                category=a.get("category", "읽을거리"),
            )
            for a in articles  # articles 리스트의 각 항목에 대해
        ]
    ```
  - **관련 개념**:
    - **리스트 컴프리헨션**: 리스트를 간결하게 생성하는 Python 문법
    - **`.get()` 메서드**: 딕셔너리에서 안전하게 값 가져오기 (키가 없어도 에러 없음)

  **`list_articles() -> List[Dict]`**

  - **역할**: 저장된 모든 기사 목록을 반환
  - **동작 원리**:
    ```python
    def list_articles(self) -> List[Dict[str, str]]:
        return [
            {
                "title": a.title,
                "url": a.url,
                "category": a.category,
                "selected": a.selected,
                "summary": a.summary,
            }
            for a in self._articles  # 모든 Article 객체를 딕셔너리로 변환
        ]
    ```

  **`delete_by_url(url: str) -> bool`**

  - **역할**: URL로 기사를 삭제
  - **동작 원리**:
    ```python
    def delete_by_url(self, url: str) -> bool:
        before = len(self._articles)  # 삭제 전 개수
        # 필터링: url이 일치하지 않는 기사만 남김
        self._articles = [a for a in self._articles if a.url != url]
        return len(self._articles) != before  # 삭제되었는지 여부 반환
    ```

**전역 인스턴스**:

```python
store = InMemoryStore()  # 애플리케이션 전체에서 공유하는 단일 인스턴스
```

- **싱글톤 패턴**: 하나의 인스턴스만 사용하여 데이터 일관성 유지

### 4.4 `app.py` - Flask 애플리케이션

#### 구조 설명

##### 1. 모듈 임포트

```python
from flask import Flask, jsonify, render_template, request
from modules import crawler, gemini, slack
from modules.store import store
from modules.common import configure_logging, register_http_logging, register_error_handlers
```

- **설명**: 필요한 Flask 기능과 프로젝트 모듈들을 가져옵니다.

##### 2. 앱 초기화

```python
app = Flask(__name__)
configure_logging()
register_http_logging(app)
register_error_handlers(app)
```

- **설명**: Flask 앱을 생성하고 공통 기능을 등록합니다.

##### 3. API 라우트 정의

**`POST /api/collect`** - 뉴스 수집

```python
@app.route('/api/collect', methods=['POST'])
def collect_news():
    articles = crawler.crawl_naver_news([])  # 뉴스 수집
    store.set_articles(articles)              # 저장소에 저장
    return jsonify({"count": len(articles)}) # 수집된 개수 반환
```

- **동작 흐름**:
  1. 클라이언트가 POST 요청 전송
  2. `crawler.crawl_naver_news()` 호출하여 뉴스 수집
  3. `store.set_articles()`로 저장소에 저장
  4. 수집된 개수를 JSON으로 반환

**`POST /api/summarize`** - 기사 요약

```python
@app.route('/api/summarize', methods=['POST'])
def summarize_news():
    data = request.get_json(silent=True) or {}  # JSON 요청 본문 파싱
    url = data.get("url")                       # "url" 키 추출
    if not url:
        return jsonify({"error": "url is required"}), 400  # 에러 응답

    article = store.get_article_by_url(url)     # 저장소에서 기사 조회
    title = article.title if article else None  # 제목 추출 (있으면)

    summary = gemini.get_summary_from_gemini(url, title=title)  # Gemini API 호출
    store.set_summary(url, summary)             # 요약 저장
    return jsonify({"url": url, "summary": summary})
```

- **동작 흐름**:
  1. 요청 본문에서 URL 추출
  2. URL이 없으면 400 에러 반환
  3. 저장소에서 기사 정보 조회
  4. Gemini API로 요약 생성
  5. 요약을 저장소에 저장하고 반환

**`GET /api/review/list`** - 기사 목록 조회

```python
@app.route('/api/review/list', methods=['GET'])
def review_list():
    return jsonify(store.list_articles())  # 모든 기사 목록 반환
```

**`POST /api/review/delete`** - 기사 삭제

```python
@app.route('/api/review/delete', methods=['POST'])
def review_delete():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.delete_by_url(url)  # 삭제 시도
    return jsonify({"deleted": ok})  # 성공 여부 반환
```

**`POST /api/review/select`** - 기사 선택/해제

```python
@app.route('/api/review/select', methods=['POST'])
def review_select():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    selected = bool(data.get("selected", True))  # 기본값: True
    if not url:
        return jsonify({"error": "url is required"}), 400
    ok = store.set_selected(url, selected)
    return jsonify({"updated": ok})
```

##### 4. 페이지 라우트

**`GET /`** - 메인 페이지

```python
@app.route('/')
def index():
    return render_template('index.html')  # templates/index.html 렌더링
```

**`GET /review`** - 검토 페이지

```python
@app.route('/review')
def review_page():
    return render_template('review.html')  # templates/review.html 렌더링
```

---

## 5. 실전 예제: 기능 추가하기

### 예제 1: 새로운 API 엔드포인트 추가

**요구사항**: 특정 카테고리의 기사만 조회하는 API 추가

#### 단계별 설명

##### 1단계: `store.py`에 메서드 추가

**추가할 코드**:

```python
def get_articles_by_category(self, category: str) -> List[Dict[str, str]]:
    """카테고리로 기사를 필터링하여 반환합니다.

    Args:
        category: 필터링할 카테고리 (그룹사, 업계, 참고, 읽을거리)

    Returns:
        해당 카테고리의 기사 목록
    """
    return [
        {
            "title": a.title,
            "url": a.url,
            "category": a.category,
            "selected": a.selected,
            "summary": a.summary,
        }
        for a in self._articles
        if a.category == category  # 카테고리가 일치하는 것만 필터링
    ]
```

**설명**:

- **리스트 컴프리헨션 필터링**: `if a.category == category` 조건으로 필터링
- **타입 힌트**: 반환 타입을 `List[Dict[str, str]]`로 명시

##### 2단계: `app.py`에 라우트 추가

**추가할 코드**:

```python
@app.route('/api/review/list/<category>', methods=['GET'])
def review_list_by_category(category: str):
    """특정 카테고리의 기사 목록을 반환합니다.

    Args:
        category: URL 경로에서 추출된 카테고리 이름

    Returns:
        JSON 형태의 기사 목록
    """
    articles = store.get_articles_by_category(category)
    return jsonify(articles)
```

**설명**:

- **URL 변수**: `<category>`는 URL 경로의 일부가 됩니다.
  - 예: `/api/review/list/그룹사` → `category = "그룹사"`
- **GET 메서드**: 데이터 조회이므로 GET 사용

##### 3단계: 테스트

**curl 명령어**:

```bash
curl http://localhost:5001/api/review/list/그룹사
```

**예상 응답**:

```json
[
  {
    "title": "현대백화점 신규 오픈",
    "url": "https://...",
    "category": "그룹사",
    "selected": false,
    "summary": ""
  }
]
```

### 예제 2: 기존 함수 수정하기

**요구사항**: `get_articles_by_category`에 정렬 기능 추가

#### 수정 전 코드

```python
def get_articles_by_category(self, category: str) -> List[Dict[str, str]]:
    return [
        {...}
        for a in self._articles
        if a.category == category
    ]
```

#### 수정 후 코드

```python
def get_articles_by_category(
    self,
    category: str,
    sort_by: str = "title"
) -> List[Dict[str, str]]:
    """카테고리로 기사를 필터링하여 반환합니다.

    Args:
        category: 필터링할 카테고리
        sort_by: 정렬 기준 ("title" 또는 "pub_date", 기본값: "title")

    Returns:
        정렬된 기사 목록
    """
    articles = [
        {
            "title": a.title,
            "url": a.url,
            "category": a.category,
            "selected": a.selected,
            "summary": a.summary,
            "pub_date": a.pub_date,  # 정렬에 필요하므로 추가
        }
        for a in self._articles
        if a.category == category
    ]

    # 정렬 로직
    if sort_by == "pub_date":
        articles.sort(key=lambda x: x.get("pub_date", ""), reverse=True)
    else:  # 기본값: title
        articles.sort(key=lambda x: x.get("title", ""))

    return articles
```

**수정 내용 설명**:

1. **매개변수 추가**: `sort_by: str = "title"` (기본값 지정)
2. **정렬 로직 추가**:
   - `list.sort()`: 리스트를 직접 수정 (반환값 없음)
   - `key=lambda x: x.get("title", "")`: 정렬 기준 지정
   - `lambda`: 간단한 함수를 한 줄로 정의
3. **pub_date 필드 추가**: 정렬에 필요하므로 딕셔너리에 포함

**관련 개념**:

- **기본 매개변수**: 함수 호출 시 생략 가능한 매개변수
- **람다 함수**: `lambda x: x.get("title")`는 다음과 동일:
  ```python
  def get_title(x):
      return x.get("title")
  ```
- **`.sort()` vs `sorted()`**:
  - `.sort()`: 리스트를 직접 수정 (원본 변경)
  - `sorted()`: 새로운 리스트 반환 (원본 유지)

---

## 6. 디버깅 팁

### 6.1 로그 확인하기

**Flask 개발 모드**:

```python
app.run(debug=True)  # 자동 재시작, 상세 에러 메시지
```

**로깅 사용**:

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("디버그 메시지")    # 상세 정보
logger.info("정보 메시지")       # 일반 정보
logger.warning("경고 메시지")    # 경고
logger.error("에러 메시지")      # 에러
```

### 6.2 일반적인 에러와 해결법

#### `ModuleNotFoundError: No module named 'modules'`

- **원인**: Python이 모듈을 찾지 못함
- **해결**: 프로젝트 루트 디렉토리에서 실행해야 함
  ```bash
  # 올바른 위치
  cd /Users/dohyun/workspace/ai/news-mvp
  python app.py
  ```

#### `AttributeError: 'NoneType' object has no attribute 'title'`

- **원인**: `None` 객체에 접근하려고 함
- **해결**: None 체크 추가
  ```python
  article = store.get_article_by_url(url)
  if article:  # None 체크
      title = article.title
  else:
      return jsonify({"error": "Article not found"}), 404
  ```

#### `KeyError: 'url'`

- **원인**: 딕셔너리에 키가 없음
- **해결**: `.get()` 메서드 사용

  ```python
  # 나쁜 예
  url = data["url"]  # KeyError 발생 가능

  # 좋은 예
  url = data.get("url")  # 없으면 None 반환
  if not url:
      return jsonify({"error": "url is required"}), 400
  ```

### 6.3 디버거 사용하기

**Python 디버거 (pdb)**:

```python
import pdb; pdb.set_trace()  # 여기서 실행이 멈춤

# 디버거 명령어:
# n (next): 다음 줄로
# s (step): 함수 안으로 들어가기
# c (continue): 계속 실행
# p 변수명: 변수 값 출력
# q (quit): 종료
```

**VS Code 디버거**:

1. 중단점(Breakpoint) 설정: 줄 번호 왼쪽 클릭
2. F5 키로 디버깅 시작
3. 변수 값 확인, 단계별 실행 가능

---

## 7. 자주 묻는 질문 (FAQ)

### Q1: `__init__.py` 파일은 왜 필요한가요?

**A**: Python이 폴더를 패키지로 인식하게 하는 파일입니다. 비어있어도 되지만, 패키지 초기화 코드를 넣을 수 있습니다.

### Q2: `@app.route()` 데코레이터는 어떻게 동작하나요?

**A**: Flask가 함수를 등록하고, 해당 URL로 요청이 오면 함수를 실행합니다. 데코레이터는 함수를 감싸서 추가 기능을 제공하는 패턴입니다.

### Q3: `g` 객체는 무엇인가요?

**A**: Flask의 컨텍스트 변수입니다. 각 HTTP 요청마다 독립적인 저장소를 제공합니다. 요청이 끝나면 자동으로 삭제됩니다.

### Q4: `Optional[Article]`은 무엇인가요?

**A**: `Article` 타입이거나 `None`일 수 있다는 의미입니다. `from typing import Optional`로 가져옵니다.

### Q5: 리스트 컴프리헨션과 일반 for 루프의 차이는?

**A**:

- **리스트 컴프리헨션**: 간결하고 빠름, 리스트 생성에 특화
  ```python
  result = [x * 2 for x in range(10)]
  ```
- **일반 for 루프**: 복잡한 로직에 적합
  ```python
  result = []
  for x in range(10):
      result.append(x * 2)
  ```

### Q6: `dataclass`는 왜 사용하나요?

**A**: 데이터를 담는 클래스를 간단하게 만들 수 있습니다. `__init__`, `__repr__` 등을 자동 생성합니다.

### Q7: 환경 변수는 어디에 저장하나요?

**A**: `.env` 파일에 저장합니다. 보안상 Git에 커밋하지 않고, `.env.sample` 파일을 템플릿으로 제공합니다.

---

## 8. 학습 리소스

### Python 기초

- [Python 공식 튜토리얼](https://docs.python.org/ko/3/tutorial/)
- [점프 투 파이썬](https://wikidocs.net/book/1)

### Flask 기초

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Flask 튜토리얼](https://flask.palletsprojects.com/tutorial/)

### 프로젝트 관련

- `README.md`: 프로젝트 개요 및 실행 방법
- `tests/`: 테스트 코드 예제 참고

---

## 9. 코드 리뷰 체크리스트

코드를 작성/수정할 때 다음을 확인하세요:

- [ ] 함수/클래스에 docstring이 있나요?
- [ ] 타입 힌트를 사용했나요?
- [ ] 에러 처리를 했나요? (None 체크, 예외 처리)
- [ ] 매직 넘버/문자열을 상수로 추출했나요?
- [ ] 함수가 하나의 책임만 가지나요? (Single Responsibility)
- [ ] 변수/함수 이름이 명확한가요?
- [ ] 불필요한 코드(주석 처리된 코드 등)를 제거했나요?

---

**마지막 업데이트**: 2025-01-XX
**작성자**: AI Assistant
**대상**: Python/Flask 주니어 개발자
