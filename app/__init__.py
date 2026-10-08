import os
import secrets
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, render_template, request, session


def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    app = Flask(__name__)
    app.config.update(SECRET_KEY=os.getenv('SECRET_KEY') or secrets.token_hex(32),
                      MAX_CONTENT_LENGTH=100_000, SESSION_COOKIE_HTTPONLY=True,
                      SESSION_COOKIE_SAMESITE='Lax')
    if test_config:
        app.config.update(test_config)

    @app.context_processor
    def csrf_context():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)
        return {'csrf_token': session['csrf_token']}

    @app.before_request
    def protect_forms():
        if request.method == 'POST':
            expected = session.get('csrf_token', '')
            supplied = request.form.get('csrf_token', '')
            if not expected or not secrets.compare_digest(expected, supplied):
                abort(400, 'Refresh the page and submit the form again.')

    from .routes import main
    app.register_blueprint(main)

    @app.errorhandler(413)
    def too_large(error):
        return render_template('index.html', error='Keep the request below 100 KB.'), 413

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-store'
        return response

    return app
