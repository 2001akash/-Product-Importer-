from .celery_app import celery
import os, json, psycopg2, tempfile
import redis

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
redis_client = redis.Redis.from_url(REDIS_URL)
DATABASE_URL = os.getenv('DATABASE_URL')

@celery.task(bind=True)
def process_csv_task(self, job_id: str, file_path: str):
    def publish(payload: dict):
        redis_client.publish(f'job:{job_id}', json.dumps(payload))

    publish({'status': 'started', 'message': 'Counting lines'})
    total = 0
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for _ in f:
            total += 1
    publish({'status': 'parsing', 'message': 'Loading CSV to temp table', 'total': total})

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('CREATE TEMP TABLE tmp_products (sku text, name text, description text, price numeric);')
    conn.commit()
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        cur.copy_expert("COPY tmp_products FROM STDIN WITH CSV HEADER", f)
    conn.commit()
    publish({'status': 'loaded_temp', 'message': 'Loaded to temp table'})

    publish({'status': 'upserting', 'message': 'Upserting into products'})
    upsert_sql = '''
    INSERT INTO products (sku, name, description, price, active, created_at, updated_at)
    SELECT sku, name, description, price, true, now(), now()
    FROM tmp_products
    ON CONFLICT (sku_lower) DO UPDATE SET
      name = EXCLUDED.name,
      description = EXCLUDED.description,
      price = EXCLUDED.price,
      updated_at = now();
    '''
    cur.execute(upsert_sql)
    conn.commit()
    publish({'status': 'done', 'message': 'Import complete', 'percent': 100})

    try:
        os.remove(file_path)
    except Exception:
        pass

@celery.task
def trigger_webhook_test(webhook_id: int):
    import requests, psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('SELECT id, url FROM webhooks WHERE id = %s', (webhook_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if not row:
        return {'status': 'not_found'}
    id_, url = row
    payload = { 'event': 'test', 'webhook_id': id_ }
    try:
        r = requests.post(url, json=payload, timeout=5)
        return {'status': r.status_code, 'text': r.text}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
