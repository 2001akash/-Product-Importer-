from .celery_app import celery
import os, json, psycopg2
import redis

# Redis connection for pub/sub progress updates
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL)

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL')


# ============================================================
#  MAIN CSV PROCESSING TASK  (REGISTERED CORRECTLY IN CELERY)
# ============================================================
@celery.task(
    name="tasks.process_csv.process_csv_task",    # <-- IMPORTANT
    bind=True
)
def process_csv_task(self, job_id: str, file_path: str):

    def publish(payload: dict):
        """Publish progress updates to WebSocket channel."""
        redis_client.publish(f"job:{job_id}", json.dumps(payload))

    # Step 1 — Count lines for progress
    publish({'status': 'started', 'message': 'Counting lines'})
    total = 0
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for _ in f:
            total += 1

    publish({
        'status': 'parsing',
        'message': 'Loading CSV into temporary table',
        'total': total
    })

    # Step 2 — Connect to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Create temporary table
    cur.execute("""
        CREATE TEMP TABLE tmp_products (
            sku TEXT,
            name TEXT,
            description TEXT,
            price NUMERIC
        );
    """)
    conn.commit()

    # Load CSV into temp table
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        cur.copy_expert("COPY tmp_products FROM STDIN WITH CSV HEADER", f)
    conn.commit()

    publish({'status': 'loaded_temp', 'message': 'CSV loaded to temp table'})

    # Step 3 — UPSERT into main table
    publish({'status': 'upserting', 'message': 'Upserting products...'})

    upsert_sql = """
    INSERT INTO products (sku, name, description, price, active, created_at, updated_at)
    SELECT sku, name, description, price, TRUE, NOW(), NOW()
    FROM tmp_products
    ON CONFLICT (sku_lower)
    DO UPDATE SET
        name = EXCLUDED.name,
        description = EXCLUDED.description,
        price = EXCLUDED.price,
        updated_at = NOW();
    """

    cur.execute(upsert_sql)
    conn.commit()

    publish({'status': 'done', 'message': 'Import complete', 'percent': 100})

    # Cleanup
    try:
        os.remove(file_path)
    except Exception:
        pass

    cur.close()
    conn.close()

    return {"status": "completed", "rows": total}


# ============================================================
#  WEBHOOK TEST TASK
# ============================================================
@celery.task(name="tasks.process_csv.trigger_webhook_test")
def trigger_webhook_test(webhook_id: int):
    import requests

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT id, url FROM webhooks WHERE id = %s", (webhook_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return {"status": "not_found"}

    wid, url = row
    payload = {"event": "test", "webhook_id": wid}

    try:
        r = requests.post(url, json=payload, timeout=5)
        return {"status": r.status_code, "text": r.text}

    except Exception as e:
        return {"status": "error", "error": str(e)}
