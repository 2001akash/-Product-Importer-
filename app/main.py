from fastapi import FastAPI
from .routers import upload, products, webhooks
from . import ws
from .database import Base, engine

# create tables (for demo; prefer using alembic in prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title='Acme Product Importer')

app.include_router(upload.router)
app.include_router(products.router)
app.include_router(webhooks.router)
app.include_router(ws.router)

@app.get('/')
def root():
    return {"message": "Acme Product Importer API"}
