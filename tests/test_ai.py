import pytest
from app.ai import AIError, analyze_sql
from google import genai
from types import SimpleNamespace


class FakeClient:
    output = '{"sql":"SELECT id FROM books","explanation":["List IDs"],"assumptions":[],"missing_information":[]}'
    def __init__(self, **kwargs):
        self.models = self
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass
    def generate_content(self, **kwargs):
        assert kwargs['config']['response_mime_type'] == 'application/json'
        return SimpleNamespace(text=self.output)


def test_sdk_boundary_and_malformed_response(monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY', 'fake-test-key')
    monkeypatch.setenv('GEMINI_MODEL', 'test-model')
    monkeypatch.setattr(genai, 'Client', FakeClient)
    assert analyze_sql('generate', 'CREATE TABLE books(id INT)', 'List IDs', '').sql == 'SELECT id FROM books'
    monkeypatch.setattr(FakeClient, 'output', '{not json')
    with pytest.raises(AIError, match='unexpected response format'):
        analyze_sql('generate', 'schema', 'question', '')
