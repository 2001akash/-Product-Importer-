from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import upload, products, webhooks

app = FastAPI(title="Acme Product Importer API")

# Add CORS middleware - THIS FIXES THE CORS ERROR
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(products.router)
app.include_router(webhooks.router)

@app.get("/")
def root():
    return {"message": "Acme Product Importer API", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy"}