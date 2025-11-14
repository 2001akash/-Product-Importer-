from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid, os
from tasks.process_csv import process_csv_task
from fastapi import status

router = APIRouter()
UPLOAD_DIR = os.getenv('UPLOAD_DIR', '/tmp/uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post('/upload')
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Only CSV allowed')
    job_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{job_id}.csv")
    # stream file to disk
    with open(save_path, 'wb') as f:
        while True:
            chunk = await file.read(1024*1024)
            if not chunk:
                break
            f.write(chunk)
    # enqueue celery task
    process_csv_task.delay(job_id=job_id, file_path=save_path)
    return {"job_id": job_id, "status": "queued"}
