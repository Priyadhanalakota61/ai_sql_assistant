# AI SQL Query Assistant

A small Flask app that drafts and explains MySQL SELECT queries using Gemini and a supplied schema. SQLGlot resolves table/column references before a draft is displayed. Nothing is executed against a database.

## Features

- Generate mode: CREATE TABLE statements + natural-language question → SELECT draft, explanation, assumptions or clarification request.
- Explain mode: CREATE TABLE statements + existing SELECT → explanation; the model must preserve the query.
- Reject multiple statements, writes, unknown schema references and malformed responses.
- Inputs/results are not saved. Synthetic-data consent precedes provider calls.

## Windows setup (Python 3.12)

From this project folder in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
notepad .env
```

Set GEMINI_API_KEY and GEMINI_MODEL privately in .env. Choose the exact model ID working with your key (the same verified model as Resume Analyzer can be tried). Never paste the key into chat or commit .env. Set SECRET_KEY to a private random value if sessions must survive restarts.

```powershell
.\.venv\Scripts\python.exe run.py
```

Open http://127.0.0.1:5001. PowerShell remains running while the local app is available. This is not a public demo link. Package-level templates avoid the prior Resume Analyzer template-path issue.

## Demo

Copy the on-page synthetic books schema. Ask: “Show titles of books with at least one available copy, sorted alphabetically.” Then use Explain mode with `SELECT title FROM books WHERE available_copies > 0 ORDER BY title;`.

To test missing information, ask for salaries with that same books schema. The app should request clarification or reject an unsupported draft, rather than display invented columns.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests use mocked AI responses, plus the real SQL parser and Flask UI. Live Gemini is not exercised. A valid draft is not proof of correct logic, actual results, performance, or safety. No schema parser is a security boundary for execution; this product does not execute SQL.

## Architecture and limits

`app/routes.py` validates consent and inputs → `validation.py` parses schema/query → `ai.py` obtains structured output → parser validates the draft → Jinja renders escaped results.

Schema limits: 20 tables, 30,000 characters, simple unqualified table names. Question limit: 4,000 characters. Existing query limit: 20,000 characters. This MVP supports one SELECT (including SELECT-based CTEs); more complex constructs can be rejected by the parser. No query history, optimization or database execution.

Gemini errors show a safe message; logs record exception type only. Provider retention is separate from this app's lack of persistence. Use synthetic, nonconfidential inputs. Local single-operator prototype; add authentication and quota controls before public hosting.

## Repository workflow

Target: Priyadhanalakota61/ai_sql_assistant, product branch ai_sql_assistant. The code is maintained on the product branch; main contains the initial repository README. CI runs the same tests on pushes/PRs.
