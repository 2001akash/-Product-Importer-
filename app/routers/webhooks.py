from fastapi import APIRouter, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import os
from tasks.process_csv import trigger_webhook_test

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class WebhookCreate(BaseModel):
    url: str
    event_type: str
    description: Optional[str] = None
    is_active: bool = True


class WebhookUpdate(BaseModel):
    url: Optional[str] = None
    event_type: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WebhookTest(BaseModel):
    test_data: dict = {"event": "test", "message": "This is a test webhook"}


@router.get("/")
async def list_webhooks(active_only: bool = False):
    """List all webhooks."""
    try:
        db = SessionLocal()
        
        query = "SELECT * FROM webhooks"
        if active_only:
            query += " WHERE is_active = true"
        query += " ORDER BY created_at DESC"
        
        result = db.execute(text(query))
        webhooks = [dict(row._mapping) for row in result]
        
        db.close()
        return {"webhooks": webhooks, "total": len(webhooks)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{webhook_id}")
async def get_webhook(webhook_id: int):
    """Get a single webhook by ID."""
    try:
        db = SessionLocal()
        result = db.execute(
            text("SELECT * FROM webhooks WHERE id = :id"),
            {"id": webhook_id}
        ).fetchone()
        db.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        return dict(result._mapping)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_webhook(webhook: WebhookCreate):
    """Create a new webhook."""
    try:
        db = SessionLocal()
        
        result = db.execute(
            text("""
                INSERT INTO webhooks (url, event_type, description, is_active)
                VALUES (:url, :event_type, :description, :is_active)
                RETURNING id
            """),
            {
                "url": webhook.url,
                "event_type": webhook.event_type,
                "description": webhook.description,
                "is_active": webhook.is_active
            }
        )
        db.commit()
        
        webhook_id = result.fetchone()[0]
        db.close()
        
        return {"id": webhook_id, "message": "Webhook created successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{webhook_id}")
async def update_webhook(webhook_id: int, webhook: WebhookUpdate):
    """Update an existing webhook."""
    try:
        db = SessionLocal()
        
        # Check if webhook exists
        existing = db.execute(
            text("SELECT id FROM webhooks WHERE id = :id"),
            {"id": webhook_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        # Build update query
        update_fields = []
        params = {"id": webhook_id}
        
        for field, value in webhook.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = NOW()")
        
        query = f"""
            UPDATE webhooks 
            SET {', '.join(update_fields)}
            WHERE id = :id
        """
        
        db.execute(text(query), params)
        db.commit()
        db.close()
        
        return {"message": "Webhook updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: int):
    """Delete a webhook."""
    try:
        db = SessionLocal()
        
        result = db.execute(
            text("DELETE FROM webhooks WHERE id = :id RETURNING id"),
            {"id": webhook_id}
        )
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        db.commit()
        db.close()
        
        return {"message": "Webhook deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: int, test_data: WebhookTest):
    """Test a webhook by sending a test request."""
    try:
        db = SessionLocal()
        
        # Get webhook
        result = db.execute(
            text("SELECT * FROM webhooks WHERE id = :id"),
            {"id": webhook_id}
        ).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        webhook = dict(result._mapping)
        db.close()
        
        # Trigger webhook test asynchronously
        task = trigger_webhook_test.delay(webhook['url'], test_data.test_data)
        
        return {
            "message": "Webhook test queued",
            "task_id": task.id,
            "webhook_url": webhook['url']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{webhook_id}/toggle")
async def toggle_webhook(webhook_id: int):
    """Toggle webhook active status."""
    try:
        db = SessionLocal()
        
        result = db.execute(
            text("""
                UPDATE webhooks 
                SET is_active = NOT is_active, updated_at = NOW()
                WHERE id = :id
                RETURNING is_active
            """),
            {"id": webhook_id}
        )
        
        row = result.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        db.commit()
        db.close()
        
        return {"message": "Webhook toggled", "is_active": row[0]}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/types")
async def get_event_types():
    """Get list of available event types."""
    return {
        "event_types": [
            "product.created",
            "product.updated",
            "product.deleted",
            "import.started",
            "import.completed",
            "import.failed"
        ]
    }