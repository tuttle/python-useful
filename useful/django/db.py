from django.db import connection


def truncate_table(model_or_tablename, cascade=False, cursor=None):
    if cursor is None:
        cursor = connection.cursor()

    if hasattr(model_or_tablename, '_meta'):
        tablename = model_or_tablename._meta.db_table
    else:
        tablename = model_or_tablename

    if cascade:
        stmt = 'TRUNCATE %s CASCADE'
    else:
        stmt = 'TRUNCATE %s'

    cursor.execute(stmt % connection.ops.quote_name(tablename))
