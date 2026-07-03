"""Supabase / Database client instance — imported by routers for database access."""

import json
import uuid
from datetime import date, datetime
from api.config import settings


def _serialize_val(val):
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, list):
        return [_serialize_val(x) for x in val]
    if isinstance(val, dict):
        return {k: _serialize_val(v) for k, v in val.items()}
    return val


class LocalResult:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count


class LocalQueryBuilder:
    def __init__(self, db_url, table_name):
        import psycopg2
        from psycopg2.extras import RealDictCursor

        self.db_url = db_url
        self.table_name = table_name
        self._operation = "select"
        self._columns = "*"
        self._count = None
        self._filters = []
        self._order = []
        self._limit = None
        self._offset = None
        self._data = None
        self._psycopg2 = psycopg2
        self._RealDictCursor = RealDictCursor

    def select(self, columns="*", count=None):
        self._operation = "select"
        self._columns = columns
        self._count = count
        return self

    def insert(self, data):
        self._operation = "insert"
        self._data = data
        return self

    def update(self, data):
        self._operation = "update"
        self._data = data
        return self

    def delete(self):
        self._operation = "delete"
        return self

    def eq(self, column, val):
        self._filters.append((f"{column} = %s", val))
        return self

    def in_(self, column, vals):
        if not vals:
            self._filters.append(("1 = 0", None))
        else:
            placeholders = ", ".join(["%s"] * len(vals))
            self._filters.append((f"{column} IN ({placeholders})", list(vals)))
        return self

    def order(self, column, desc=False):
        direction = "DESC" if desc else "ASC"
        self._order.append(f"{column} {direction}")
        return self

    def range(self, start, end):
        self._offset = start
        self._limit = end - start + 1
        return self

    def limit(self, n):
        self._limit = n
        return self

    def _convert_val(self, v):
        if v == "now()" or v == "now":
            return datetime.utcnow().isoformat()
        if isinstance(v, (dict, list)):
            return json.dumps(v)
        return v

    def execute(self):
        conn = self._psycopg2.connect(self.db_url)
        try:
            with conn.cursor(cursor_factory=self._RealDictCursor) as cur:
                where_sql = ""
                params = []
                if self._filters:
                    clauses = []
                    for clause, p in self._filters:
                        clauses.append(clause)
                        if p is not None:
                            if isinstance(p, list):
                                params.extend(p)
                            else:
                                params.append(p)
                    where_sql = " WHERE " + " AND ".join(clauses)

                if self._operation == "select":
                    count_val = None
                    if self._count == "exact":
                        cur.execute(
                            f"SELECT COUNT(*) as cnt FROM {self.table_name}{where_sql}",
                            params,
                        )
                        row = cur.fetchone()
                        count_val = row["cnt"] if row else 0

                    sql = f"SELECT {self._columns} FROM {self.table_name}{where_sql}"
                    if self._order:
                        sql += " ORDER BY " + ", ".join(self._order)
                    if self._limit is not None:
                        sql += f" LIMIT {self._limit}"
                    if self._offset is not None:
                        sql += f" OFFSET {self._offset}"

                    cur.execute(sql, params)
                    rows = [_serialize_val(dict(r)) for r in cur.fetchall()]
                    return LocalResult(rows, count=count_val)

                elif self._operation == "insert":
                    rows_to_insert = (
                        self._data if isinstance(self._data, list) else [self._data]
                    )
                    inserted = []
                    for row in rows_to_insert:
                        cols = list(row.keys())
                        converted_vals = [self._convert_val(row[c]) for c in cols]
                        placeholders = ", ".join(["%s"] * len(cols))
                        col_names = ", ".join(cols)
                        sql = f"INSERT INTO {self.table_name} ({col_names}) VALUES ({placeholders}) RETURNING *"
                        cur.execute(sql, converted_vals)
                        res = cur.fetchone()
                        if res:
                            inserted.append(_serialize_val(dict(res)))
                    conn.commit()
                    return LocalResult(inserted)

                elif self._operation == "update":
                    cols = list(self._data.keys())
                    converted_vals = [self._convert_val(self._data[c]) for c in cols]
                    set_clauses = ", ".join([f"{c} = %s" for c in cols])
                    sql = f"UPDATE {self.table_name} SET {set_clauses}{where_sql} RETURNING *"
                    cur.execute(sql, converted_vals + params)
                    rows = [_serialize_val(dict(r)) for r in cur.fetchall()]
                    conn.commit()
                    return LocalResult(rows)

                elif self._operation == "delete":
                    sql = f"DELETE FROM {self.table_name}{where_sql} RETURNING *"
                    cur.execute(sql, params)
                    rows = [_serialize_val(dict(r)) for r in cur.fetchall()]
                    conn.commit()
                    return LocalResult(rows)
        finally:
            conn.close()


class LocalPostgresAdapter:
    def __init__(self, db_url):
        self.db_url = db_url

    def table(self, table_name):
        return LocalQueryBuilder(self.db_url, table_name)


if settings.database_url:
    supabase = LocalPostgresAdapter(settings.database_url)
else:
    from supabase import create_client

    if not settings.supabase_url or not settings.supabase_service_key:
        raise ValueError(
            "Either DATABASE_URL or (SUPABASE_URL and SUPABASE_SERVICE_KEY) must be provided."
        )
    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
