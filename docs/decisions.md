# Confirmed scope and implementation decisions

The user asked to build AI SQL Query Assistant and Smart Library System, then specified separate GitHub repositories ai_sql_assistant and smart_library_system.
The immediately preceding proposed MVP is used as the implementation scope.

- Flask UI and Gemini integration; MySQL query dialect.
- Generate a SELECT draft from CREATE TABLE schema and a question; explain an existing SELECT query.
- No query execution, database connection, query history or optimization claims. MySQL is the SQL dialect, not a persistence requirement for this MVP.
- No inputs/results persisted server-side. They are sent to Gemini only after synthetic-data consent. Session contains only a CSRF token.
- SQLGlot checks parse shape and table/column resolution. This does not verify query semantics, performance or execution safety.
- No production schema or real data in this free-tier demo. No row data requested.
- Credentials and model ID are configurable; no model availability assumed.
- Local single-operator portfolio demo; no login, multi-user access or public deployment included.
