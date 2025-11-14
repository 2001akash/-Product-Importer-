from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy import func

def get_products(db: Session, skip: int = 0, limit: int = 50, filters: dict = None):
    q = db.query(models.Product)
    if filters:
        if filters.get('sku'):
            q = q.filter(func.lower(models.Product.sku) == filters['sku'].lower())
        if filters.get('name'):
            q = q.filter(models.Product.name.ilike(f"%{filters['name']}%"))
        if filters.get('active') is not None:
            q = q.filter(models.Product.active == filters['active'])
    return q.order_by(models.Product.id.desc()).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    db_obj = models.Product(**product.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_product_by_id(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def update_product(db: Session, product_id: int, data: dict):
    db_obj = get_product_by_id(db, product_id)
    if not db_obj:
        return None
    for k,v in data.items():
        setattr(db_obj, k, v)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_product(db: Session, product_id: int):
    db_obj = get_product_by_id(db, product_id)
    if db_obj:
        db.delete(db_obj)
        db.commit()
        return True
    return False

def list_webhooks(db: Session):
    return db.query(models.Webhook).order_by(models.Webhook.id.desc()).all()

def create_webhook(db: Session, data: dict):
    obj = models.Webhook(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_webhook(db: Session, id: int):
    return db.query(models.Webhook).filter(models.Webhook.id == id).first()

def update_webhook(db: Session, id: int, data: dict):
    obj = get_webhook(db, id)
    if not obj:
        return None
    for k,v in data.items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def delete_webhook(db: Session, id: int):
    obj = get_webhook(db, id)
    if obj:
        db.delete(obj)
        db.commit()
        return True
    return False
