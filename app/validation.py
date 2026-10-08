import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.errors import ParseError, OptimizeError


class InputError(ValueError):
    pass


def parse_schema(text):
    if not text.strip() or len(text) > 30_000:
        raise InputError('Provide CREATE TABLE statements, up to 30,000 characters.')
    try:
        statements = sqlglot.parse(text, read='mysql')
        tables = {}
        for statement in statements:
            if not isinstance(statement, exp.Create) or statement.args.get('kind') != 'TABLE':
                raise InputError('Schema input accepts CREATE TABLE statements only.')
            schema = statement.this
            if not isinstance(schema, exp.Schema) or not isinstance(schema.this, exp.Table):
                raise InputError('Include column definitions in each CREATE TABLE statement.')
            table = schema.this
            if table.db or table.catalog:
                raise InputError('Use simple table names without database prefixes.')
            name = table.name.lower()
            if name in tables or statement.args.get('expression'):
                raise InputError('Use distinct table definitions without AS SELECT.')
            columns = {}
            for column in schema.expressions:
                if isinstance(column, exp.ColumnDef):
                    key = column.name.lower()
                    if key in columns:
                        raise InputError('Duplicate column names are unsupported.')
                    columns[key] = column.args['kind'].sql(dialect='mysql')
            if not columns:
                raise InputError('Each table must include named columns and types.')
            tables[name] = columns
        if not tables or len(tables) > 20:
            raise InputError('Provide between 1 and 20 tables.')
        return tables
    except (ParseError, KeyError) as exc:
        raise InputError('The MySQL schema could not be parsed. Check the CREATE TABLE syntax.') from exc


def validate_sql(sql, tables):
    if not sql.strip() or len(sql) > 20_000:
        raise InputError('Provide one SQL query, up to 20,000 characters.')
    try:
        statements = sqlglot.parse(sql, read='mysql')
        if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.Union, exp.Intersect, exp.Except)):
            raise InputError('This MVP accepts one SELECT query, including SELECT-based CTEs.')
        query = statements[0]
        for node in query.walk():
            if isinstance(node, (exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop, exp.Command, exp.Into, exp.Lock)):
                raise InputError('Only a SELECT draft without writes or locking is supported.')
            if isinstance(node, exp.Table) and (node.db or node.catalog):
                raise InputError('Database-qualified names are unsupported.')
            if isinstance(node, exp.Anonymous) and node.name.upper() in {'SLEEP', 'BENCHMARK', 'LOAD_FILE'}:
                raise InputError('This function is unsupported in the demo.')
        # Resolve aliases, CTEs, tables and columns against the supplied schema.
        # Parsing/qualification is a consistency check, not execution or proof of correctness.
        qualify(query.copy(), dialect='mysql', schema=tables,
                validate_qualify_columns=True, infer_schema=False)
        return sql.strip()
    except (ParseError, OptimizeError) as exc:
        raise InputError('The SQL cannot be resolved against the supplied schema. Check table and column names.') from exc
