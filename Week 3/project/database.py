import os

import psycopg2


def get_db_connection():
    return psycopg2.connect(
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "8001"),
        database=os.getenv("DB_NAME", "db"),
    )

