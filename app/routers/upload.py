from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from celery.result import AsyncResult
import os
import shutil
from tasks.process_csv import process_csv_task
import json
import asyncio

router = APIRouter(tags=["upload"])

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file and queue it for processing.
    Returns job_id for tracking.
    """
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Queue the task
        task = process_csv_task.delay(file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "job_id": task.id,
                "status": "queued",
                "filename": file.filename
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    """
    Get the current status of an upload job.
    """
    try:
        result = AsyncResult(job_id)
        
        if result.ready():
            if result.successful():
                return {
                    "status": "completed",
                    "progress": 100,
                    "result": result.result
                }
            else:
                return {
                    "status": "failed",
                    "progress": 0,
                    "error": str(result.info)
                }
        else:
            # Check for progress updates
            info = result.info
            if isinstance(info, dict):
                return {
                    "status": "processing",
                    "progress": info.get("progress", 0),
                    "current": info.get("current", 0),
                    "total": info.get("total", 0),
                    "message": info.get("message", "Processing...")
                }
            else:
                return {
                    "status": "processing",
                    "progress": 0,
                    "message": "Starting..."
                }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/progress/{job_id}")
async def stream_upload_progress(job_id: str):
    """
    Server-Sent Events (SSE) endpoint for real-time progress updates.
    """
    async def event_generator():
        result = AsyncResult(job_id)
        
        while not result.ready():
            info = result.info
            
            if isinstance(info, dict):
                data = {
                    "status": "processing",
                    "progress": info.get("progress", 0),
                    "current": info.get("current", 0),
                    "total": info.get("total", 0),
                    "message": info.get("message", "Processing...")
                }
            else:
                data = {
                    "status": "processing",
                    "progress": 0,
                    "message": "Starting..."
                }
            
            yield f"data: {json.dumps(data)}\n\n"
            await asyncio.sleep(0.5)  # Poll every 500ms
        
        # Final result
        if result.successful():
            final_data = {
                "status": "completed",
                "progress": 100,
                "result": result.result
            }
        else:
            final_data = {
                "status": "failed",
                "progress": 0,
                "error": str(result.info)
            }
        
        yield f"data: {json.dumps(final_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )