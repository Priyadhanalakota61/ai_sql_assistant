from flask import Blueprint, current_app, render_template, request
from .ai import AIError, analyze_sql
from .validation import InputError, parse_schema, validate_sql

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def home():
    values = {'mode': 'generate', 'schema': '', 'question': '', 'query': ''}
    if request.method == 'GET':
        return render_template('index.html', values=values)
    values.update({name: request.form.get(name, '').strip() for name in values})
    try:
        if request.form.get('consent') != 'yes':
            raise InputError('Confirm that these inputs are synthetic and contain no confidential data.')
        if values['mode'] not in {'generate', 'explain'}:
            raise InputError('Choose Generate or Explain.')
        tables = parse_schema(values['schema'])
        if values['mode'] == 'generate' and (not values['question'] or len(values['question']) > 4000):
            raise InputError('Enter a question, up to 4,000 characters.')
        if values['mode'] == 'explain':
            validate_sql(values['query'], tables)
        analyzer = current_app.config.get('SQL_ANALYZER', analyze_sql)
        result = analyzer(values['mode'], values['schema'], values['question'], values['query'])
        if values['mode'] == 'explain' and result.sql.strip() != values['query'].strip():
            raise AIError('The model changed the query instead of explaining it. Try again.')
        if result.sql:
            validate_sql(result.sql, tables)
        elif not result.missing_information:
            raise AIError('The model returned neither a query nor a clarification request.')
        return render_template('index.html', values=values, result=result)
    except (InputError, AIError) as exc:
        return render_template('index.html', values=values, error=str(exc)), 400


@main.get('/health')
def health():
    return {'status': 'ok', 'product': 'ai_sql_assistant'}
