from celery import shared_task
import psycopg2
import os
import csv
from io import StringIO
import requests

@shared_task(bind=True)
def process_csv_task(self, file_path: str):
    """
    Process CSV file with progress reporting.
    """
    conn = None
    try:
        # Report initial progress
        self.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'current': 0, 'total': 0, 'message': 'Starting import...'}
        )
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cur = conn.cursor()
        
        # Get database columns
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'products'
            ORDER BY ordinal_position
        """)
        db_columns = [row[0] for row in cur.fetchall() if row[0] not in ['id', 'created_at', 'updated_at']]
        
        # Count total rows for progress
        with open(file_path, 'r', encoding='utf-8') as f:
            total_rows = sum(1 for _ in f) - 1  # Exclude header
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 5, 'current': 0, 'total': total_rows, 'message': f'Reading {total_rows:,} rows...'}
        )
        
        # Read CSV
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            csv_headers = reader.fieldnames
        
        # Determine usable columns
        usable_columns = [col for col in csv_headers if col in db_columns]
        
        if not usable_columns:
            raise ValueError(f"No matching columns between CSV and database")
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'current': 0, 'total': total_rows, 'message': f'Validating data...'}
        )
        
        # Process CSV
        with open(file_path, 'r', encoding='utf-8') as input_file:
            reader = csv.DictReader(input_file)
            
            output = StringIO()
            writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(usable_columns)
            
            row_num = 0
            for row in reader:
                row_num += 1
                try:
                    values = [row.get(col, '') for col in usable_columns]
                    writer.writerow(values)
                    
                    # Update progress every 10,000 rows
                    if row_num % 10000 == 0:
                        progress = 10 + int((row_num / total_rows) * 70)  # 10-80%
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'progress': progress,
                                'current': row_num,
                                'total': total_rows,
                                'message': f'Processing row {row_num:,} of {total_rows:,}...'
                            }
                        )
                except Exception as e:
                    print(f"Warning: Skipping row {row_num}: {e}")
                    continue
            
            output.seek(0)
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'current': row_num, 'total': total_rows, 'message': 'Importing to database...'}
        )
        
        # Create temp table
        temp_cols = ', '.join([f"{col} TEXT" for col in usable_columns])
        cur.execute(f"""
            CREATE TEMP TABLE tmp_products ({temp_cols}) ON COMMIT DROP
        """)
        
        # Copy data
        cur.copy_expert(
            sql="COPY tmp_products FROM STDIN WITH (FORMAT CSV, HEADER true, QUOTE '\"', ESCAPE '\"')",
            file=output
        )
        
        self.update_state(
            state='PROGRESS',
            meta={'progress': 90, 'current': row_num, 'total': total_rows, 'message': 'Saving to database...'}
        )
        
        # Build INSERT with upsert on SKU
        columns_str = ', '.join(usable_columns)
        select_str = ', '.join([f"NULLIF(TRIM({col}), '')" if col not in ['sku', 'name'] else col for col in usable_columns])
        
        # Check if SKU unique constraint exists
        cur.execute("""
            SELECT 1 FROM pg_indexes 
            WHERE indexname = 'products_sku_lower_unique'
        """)
        has_sku_unique = cur.fetchone() is not None
        
        if has_sku_unique and 'sku' in usable_columns:
            # Upsert on SKU
            update_cols = [col for col in usable_columns if col not in ['sku', 'id']]
            update_str = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])
            
            cur.execute(f"""
                INSERT INTO products ({columns_str})
                SELECT {select_str}
                FROM tmp_products
                WHERE sku IS NOT NULL AND TRIM(sku) != ''
                ON CONFLICT (LOWER(sku)) DO UPDATE SET
                    {update_str},
                    updated_at = NOW()
            """)
        else:
            # Simple insert
            cur.execute(f"""
                INSERT INTO products ({columns_str})
                SELECT {select_str}
                FROM tmp_products
                WHERE sku IS NOT NULL AND TRIM(sku) != ''
            """)
        
        rows_inserted = cur.rowcount
        conn.commit()
        
        cur.close()
        conn.close()
        
        # Delete file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            'status': 'success',
            'rows_processed': rows_inserted,
            'file': file_path,
            'columns_used': usable_columns
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        
        error_msg = f"Error processing CSV: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


@shared_task
def trigger_webhook_test(webhook_url: str, data: dict):
    """Test webhook endpoint."""
    try:
        response = requests.post(
            webhook_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        return {
            'status': 'success',
            'status_code': response.status_code,
            'response': response.text[:500],
            'webhook_url': webhook_url
        }
    except requests.exceptions.RequestException as e:
        return {
            'status': 'error',
            'error': str(e),
            'webhook_url': webhook_url
        }