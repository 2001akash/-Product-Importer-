from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import crud, schemas
from typing import Optional

router = APIRouter(prefix='/products')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get('', response_model=list[schemas.ProductOut])
def list_products(
    sku: Optional[str] = None,
    name: Optional[str] = None,
    active: Optional[bool] = None,
    page: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    skip = page * limit
    filters = {k:v for k,v in [('sku',sku), ('name',name), ('active', active)] if v is not None}
    return crud.get_products(db, skip=skip, limit=limit, filters=filters)

@router.post('', response_model=schemas.ProductOut)
def create_product(p: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, p)

@router.put('/{product_id}', response_model=schemas.ProductOut)
def update_product(product_id: int, p: schemas.ProductUpdate, db: Session = Depends(get_db)):
    obj = crud.update_product(db, product_id, p.dict(exclude_unset=True))
    if not obj:
        raise HTTPException(status_code=404, detail='Not found')
    return obj

@router.delete('/{product_id}')
def delete_product(product_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_product(db, product_id)
    if not ok:
        raise HTTPException(status_code=404, detail='Not found')
    return {'status': 'deleted'}

@router.post('/delete-all')
def delete_all_products(db: Session = Depends(get_db)):
    db.execute('TRUNCATE TABLE products RESTART IDENTITY')
    db.commit()
    return {'status': 'deleted_all'}
