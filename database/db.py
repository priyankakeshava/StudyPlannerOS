import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def connect():
    password = os.getenv("STUDYOS_DB_PASSWORD")
    if password is None:
        raise RuntimeError("STUDYOS_DB_PASSWORD is not set. Copy .env.example to .env and configure MySQL.")
    return mysql.connector.connect(
        host=os.getenv("STUDYOS_DB_HOST", "127.0.0.1"),
        port=int(os.getenv("STUDYOS_DB_PORT", "3306")),
        user=os.getenv("STUDYOS_DB_USER", "root"),
        password=password,
        database=os.getenv("STUDYOS_DB_NAME", "studyos"),
    )


def fetch_all(query, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def execute(query, params=()):
    conn = connect()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
