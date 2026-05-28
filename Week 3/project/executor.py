import logging
import time

from psycopg2.extras import RealDictCursor

from database import get_db_connection


def _normalize_rows(rows):
    if len(rows) == 1 and len(rows[0]) == 1:
        return next(iter(rows[0].values()))
    return rows


def run_query(sql: str):
    start_time = time.time()
    logging.info("Executing SQL: %s", sql)
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            rows = [dict(row) for row in cur.fetchall()]
            result = _normalize_rows(rows)
            logging.info("Query executed successfully in %.2fs", time.time() - start_time)
            return result
    except Exception:
        conn.rollback()
        logging.exception("Query execution failed")
        raise
    finally:
        conn.close()

