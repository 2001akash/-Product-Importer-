from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter(prefix="/products", tags=["products"])

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: Optional[int] = 0
    active: bool = True


class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    stock_quantity: Optional[int] = None
    active: Optional[bool] = None


class ProductResponse(BaseModel):
    id: int
    sku: str
    name: str
    description: Optional[str]
    price: Optional[float]
    image_url: Optional[str]
    category: Optional[str]
    stock_quantity: Optional[int]
    active: bool
    created_at: str
    updated_at: str


@router.get("/")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    sku: Optional[str] = None,
    category: Optional[str] = None,
    active: Optional[bool] = None
):
    """
    List products with pagination and filtering.
    """
    try:
        db = SessionLocal()
        offset = (page - 1) * limit
        
        # Build WHERE clause
        where_clauses = []
        params = {}
        
        if search:
            where_clauses.append("(LOWER(name) LIKE :search OR LOWER(description) LIKE :search OR LOWER(sku) LIKE :search)")
            params['search'] = f"%{search.lower()}%"
        
        if sku:
            where_clauses.append("LOWER(sku) = :sku")
            params['sku'] = sku.lower()
        
        if category:
            where_clauses.append("LOWER(category) = :category")
            params['category'] = category.lower()
        
        if active is not None:
            where_clauses.append("active = :active")
            params['active'] = active
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Get total count
        count_query = f"SELECT COUNT(*) FROM products WHERE {where_sql}"
        total = db.execute(text(count_query), params).scalar()
        
        # Get products
        query = f"""
            SELECT id, sku, name, description, price, image_url, category, 
                   stock_quantity, active, created_at, updated_at
            FROM products 
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params.update({'limit': limit, 'offset': offset})
        
        result = db.execute(text(query), params)
        products = [dict(row._mapping) for row in result]
        
        db.close()
        
        return {
            "products": products,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{product_id}")
async def get_product(product_id: int):
    """Get a single product by ID."""
    try:
        db = SessionLocal()
        result = db.execute(
            text("SELECT * FROM products WHERE id = :id"),
            {"id": product_id}
        ).fetchone()
        db.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return dict(result._mapping)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_product(product: ProductCreate):
    """Create a new product."""
    try:
        db = SessionLocal()
        
        # Check if SKU already exists (case-insensitive)
        existing = db.execute(
            text("SELECT id FROM products WHERE LOWER(sku) = LOWER(:sku)"),
            {"sku": product.sku}
        ).fetchone()
        
        if existing:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
        
        # Insert product
        result = db.execute(
            text("""
                INSERT INTO products (sku, name, description, price, image_url, category, stock_quantity, active)
                VALUES (:sku, :name, :description, :price, :image_url, :category, :stock_quantity, :active)
                RETURNING id
            """),
            {
                "sku": product.sku,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_url": product.image_url,
                "category": product.category,
                "stock_quantity": product.stock_quantity,
                "active": product.active
            }
        )
        db.commit()
        
        product_id = result.fetchone()[0]
        db.close()
        
        return {"id": product_id, "message": "Product created successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{product_id}")
async def update_product(product_id: int, product: ProductUpdate):
    """Update an existing product."""
    try:
        db = SessionLocal()
        
        # Check if product exists
        existing = db.execute(
            text("SELECT id FROM products WHERE id = :id"),
            {"id": product_id}
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Build update query dynamically
        update_fields = []
        params = {"id": product_id}
        
        for field, value in product.dict(exclude_unset=True).items():
            if value is not None:
                update_fields.append(f"{field} = :{field}")
                params[field] = value
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_fields.append("updated_at = NOW()")
        
        query = f"""
            UPDATE products 
            SET {', '.join(update_fields)}
            WHERE id = :id
        """
        
        db.execute(text(query), params)
        db.commit()
        db.close()
        
        return {"message": "Product updated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{product_id}")
async def delete_product(product_id: int):
    """Delete a product."""
    try:
        db = SessionLocal()
        
        result = db.execute(
            text("DELETE FROM products WHERE id = :id RETURNING id"),
            {"id": product_id}
        )
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.commit()
        db.close()
        
        return {"message": "Product deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/")
async def bulk_delete_products():
    """Delete ALL products (with caution!)."""
    try:
        db = SessionLocal()
        
        result = db.execute(text("DELETE FROM products RETURNING id"))
        count = len(result.fetchall())
        
        db.commit()
        db.close()
        
        return {"message": f"Deleted {count} products", "count": count}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_stats():
    """Get product statistics."""
    try:
        db = SessionLocal()
        
        stats = db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE active = true) as active,
                COUNT(*) FILTER (WHERE active = false) as inactive,
                COUNT(DISTINCT category) as categories
            FROM products
        """)).fetchone()
        
        db.close()
        
        return dict(stats._mapping)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))