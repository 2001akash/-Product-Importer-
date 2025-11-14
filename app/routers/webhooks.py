from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import crud, schemas
from tasks.process_csv import trigger_webhook_test

router = APIRouter(prefix='/webhooks')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('', response_model=list[schemas.WebhookOut])
def list_webhooks(db: Session = Depends(get_db)):
    return crud.list_webhooks(db)

@router.post('', response_model=schemas.WebhookOut)
def create_webhook(w: schemas.WebhookBase, db: Session = Depends(get_db)):
    payload = {
        'url': str(w.url),
        'event_types': w.event_types,
        'enabled': w.enabled,
    }
    return crud.create_webhook(db, payload)

@router.post('/{id}/test')
def test_webhook(id: int, db: Session = Depends(get_db)):
    wh = crud.get_webhook(db, id)
    if not wh:
        raise HTTPException(status_code=404, detail='Webhook not found')
    trigger_webhook_test.delay(wh.id)
    return {'status': 'test_enqueued'}

@router.put('/{id}')
def update_webhook(id: int, w: schemas.WebhookBase, db: Session = Depends(get_db)):
    obj = crud.update_webhook(db, id, w.dict())
    if not obj:
        raise HTTPException(status_code=404, detail='Webhook not found')
    return obj

@router.delete('/{id}')
def delete_webhook(id: int, db: Session = Depends(get_db)):
    ok = crud.delete_webhook(db, id)
    if not ok:
        raise HTTPException(status_code=404, detail='Webhook not found')
    return {'status': 'deleted'}
