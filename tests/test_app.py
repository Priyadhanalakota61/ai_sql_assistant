import pytest
from app import create_app
from app.ai import AIError, SQLResult
from app.validation import InputError, parse_schema, validate_sql

SCHEMA = 'CREATE TABLE books (id INT PRIMARY KEY, title VARCHAR(200), available_copies INT);'


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only'})
    return app.test_client()


def post(client, **overrides):
    client.get('/')
    with client.session_transaction() as session:
        token = session['csrf_token']
    data = dict(csrf_token=token, consent='yes', mode='generate', schema=SCHEMA,
                question='List book titles', query='')
    data.update(overrides)
    return client.post('/', data=data)


def test_schema_and_valid_queries():
    tables = parse_schema(SCHEMA)
    for sql in ['SELECT title FROM books', 'SELECT b.title FROM books b WHERE b.available_copies > 0',
                'WITH b AS (SELECT title FROM books) SELECT title FROM b',
                'SELECT COUNT(*) FROM books']:
        assert validate_sql(sql, tables) == sql


@pytest.mark.parametrize('sql', ['SELECT salary FROM books', 'SELECT title FROM unknown_table',
    'DROP TABLE books', 'DELETE FROM books', 'SELECT title FROM books; SELECT id FROM books',
    'SELECT title FROM other.books', "SELECT title INTO OUTFILE '/tmp/x' FROM books"])
def test_reject_invalid_or_unsupported_queries(sql):
    with pytest.raises(InputError):
        validate_sql(sql, parse_schema(SCHEMA))


@pytest.mark.parametrize('schema', ['', 'DROP TABLE books;', 'CREATE TABLE books AS SELECT 1;',
    'CREATE TABLE books (id INT); CREATE TABLE books (name TEXT);'])
def test_schema_rejections(schema):
    with pytest.raises(InputError):
        parse_schema(schema)


def test_generation_and_escaping(client):
    client.application.config['SQL_ANALYZER'] = lambda *args: SQLResult(sql='SELECT title FROM books',
        explanation=['<script>alert(1)</script>'], assumptions=[], missing_information=[])
    response = post(client)
    assert response.status_code == 200
    assert b'&lt;script&gt;' in response.data
    assert b'<script>' not in response.data


def test_unknown_model_column_rejected(client):
    client.application.config['SQL_ANALYZER'] = lambda *args: SQLResult(sql='SELECT salary FROM books',
        explanation=[], assumptions=[], missing_information=[])
    assert post(client).status_code == 400


def test_missing_schema_information(client):
    client.application.config['SQL_ANALYZER'] = lambda *args: SQLResult(sql='', explanation=[],
        assumptions=[], missing_information=['No salary column supplied.'])
    assert b'No salary column' in post(client).data


def test_preflight_prevents_ai_calls(client):
    def unexpected(*args):
        raise AssertionError('AI must not be called')
    client.application.config['SQL_ANALYZER'] = unexpected
    assert post(client, consent='').status_code == 400
    assert post(client, schema='').status_code == 400
    assert post(client, mode='explain', query='DELETE FROM books').status_code == 400


def test_csrf_and_missing_key(client, monkeypatch):
    assert client.post('/', data={}).status_code == 400
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    assert b'Set GEMINI_API_KEY' in post(client).data


def test_explain_must_preserve_query(client):
    client.application.config['SQL_ANALYZER'] = lambda *args: SQLResult(sql='SELECT id FROM books',
        explanation=[], assumptions=[], missing_information=[])
    assert b'changed the query' in post(client, mode='explain', query='SELECT title FROM books').data


def test_ai_failure(client):
    def fail(*args):
        raise AIError('Quota unavailable')
    client.application.config['SQL_ANALYZER'] = fail
    assert b'Quota unavailable' in post(client).data
