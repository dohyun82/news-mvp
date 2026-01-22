# Repository Guidelines

## Project Structure & Module Organization
- `app.py` is the Flask entry point and registers Blueprints.
- `apps/` holds feature modules (`news/`, `logs/`) with `routes.py`, `services.py`, and feature templates.
- `core/` contains shared app concerns such as configuration and request/response helpers.
- `shared/` hosts reusable integrations (AI clients, Slack/Datadog, storage abstractions).
- `modules/` is a legacy area being migrated; existing logic (crawler, keyword store) still lives here.
- `templates/` and `static/` contain shared Jinja2 layouts and assets.
- `data/keywords.json` stores keyword/category mappings.
- `tests/` contains unit tests (`test_*.py`).

## Build, Test, and Development Commands
- Create and activate a venv:
  - `python3 -m venv venv`
  - `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Create local env file: `cp .env.sample .env`
- Run the app: `flask --app app run --host=0.0.0.0 --port 5001`
- Run tests: `python -m unittest discover -s tests`

## Coding Style & Naming Conventions
- Python 3.9+ with 4-space indentation.
- Use `snake_case` for functions and modules; keep Flask routes grouped by Blueprint.
- Templates live under each feature’s `templates/` plus shared `templates/` at the root.
- No enforced formatter/linter is configured; follow PEP 8 conventions and keep changes readable.

## Testing Guidelines
- Tests use the built-in `unittest` framework.
- Name tests `tests/test_*.py`, and keep test classes/methods descriptive.
- Mock external integrations (Naver API, Slack, OpenAI) to avoid real network calls in unit tests.

## Commit & Pull Request Guidelines
- Follow the existing commit style: `feat:`, `refactor:`, `docs:`, `bugfix:`, `chore:` with short, descriptive summaries (Korean is common in history).
- PRs should include: a brief summary, how you tested, and screenshots/GIFs for UI changes.
- Call out changes to `data/keywords.json` or `.env.sample` explicitly in the PR description.

## Security & Configuration Tips
- Never commit real credentials. Use `.env` locally and keep `.env.sample` up to date.
- Required keys include `OPENAI_API_KEY`, `SLACK_BOT_TOKEN`, `NAVER_API_CLIENT_ID`, and Datadog tokens as needed.
