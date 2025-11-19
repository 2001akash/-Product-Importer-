# Acme Product Importer

A high-performance web application for importing and managing large product catalogs (500,000+ records) with real-time progress tracking, built with FastAPI, Celery, PostgreSQL, and Redis.

## 🚀 Live Demo

**Live Application**: [Your Render URL here]

**Features**:
- 📤 CSV Upload with real-time progress tracking (SSE)
- 📊 Product Management (CRUD operations with pagination & filtering)
- 🔗 Webhook Management (configure, test, enable/disable)
- ⚡ Handles 500K+ rows in ~20 seconds
- 🔄 Async processing with Celery
- 🎯 SKU de-duplication (case-insensitive)

## 📋 Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Task Queue**: Celery with Redis
- **Database**: PostgreSQL 15
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Docker + Render

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Browser   │────▶│  FastAPI Web │────▶│  PostgreSQL │
│  (Frontend) │◀────│   (Backend)  │◀────│  (Database) │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐     ┌─────────────┐
                    │    Redis     │────▶│   Celery    │
                    │  (Broker)    │◀────│   Worker    │
                    └──────────────┘     └─────────────┘
```

## ✨ Features

### Story 1: File Upload
- Upload CSV files up to 500K+ records
- Real-time progress indicator with Server-Sent Events (SSE)
- Automatic SKU de-duplication (case-insensitive)
- Handles duplicate products with upsert logic
- Active/Inactive status support

### Story 2: Product Management
- View products with pagination (50 per page)
- Search by name, SKU, or description
- Filter by category and active status
- Create, update, and delete products
- Inline editing with modal forms

### Story 3: Bulk Operations
- Delete all products with double confirmation
- Visual feedback and notifications
- Safe operation with transaction rollback

### Story 4: Webhook Management
- Configure multiple webhooks per event type
- Test webhooks with custom payloads
- Enable/disable webhooks
- Support for multiple event types:
  - `product.created`
  - `product.updated`
  - `product.deleted`
  - `import.started`
  - `import.completed`
  - `import.failed`

## 🚀 Quick Start (Local Development)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)

### Run with Docker

```bash
# Clone the repository
git clone <your-repo-url>
cd product-importer

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access the application
# Frontend: http://localhost:8000/static/index.html
# API Docs: http://localhost:8000/docs
# API: http://localhost:8000
```

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost:5432/acme
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
REDIS_URL=redis://localhost:6379/0
```

## 📊 Performance

- **Upload Speed**: ~25,000 rows/second using PostgreSQL COPY
- **De-duplication**: In-memory hash table (O(n) complexity)
- **Database**: Optimized indexes on SKU, name, category, active status
- **Processing**: 500,000 rows processed in ~18-20 seconds

## 🗄️ Database Schema

### Products Table
```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    sku TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    price NUMERIC(12,2),
    image_url TEXT,
    category TEXT,
    stock_quantity INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Case-insensitive unique constraint on SKU
CREATE UNIQUE INDEX products_sku_lower_unique ON products (LOWER(sku));
```

### Webhooks Table
```sql
CREATE TABLE webhooks (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    event_type TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 📡 API Endpoints

### Upload
- `POST /upload` - Upload CSV file
- `GET /upload/status/{job_id}` - Check upload status
- `GET /upload/progress/{job_id}` - Real-time progress stream (SSE)

### Products
- `GET /products` - List products (with pagination & filters)
- `GET /products/{id}` - Get single product
- `POST /products` - Create product
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `DELETE /products` - Bulk delete all products
- `GET /products/stats/summary` - Get statistics

### Webhooks
- `GET /webhooks` - List all webhooks
- `GET /webhooks/{id}` - Get single webhook
- `POST /webhooks` - Create webhook
- `PUT /webhooks/{id}` - Update webhook
- `DELETE /webhooks/{id}` - Delete webhook
- `POST /webhooks/{id}/test` - Test webhook
- `POST /webhooks/{id}/toggle` - Enable/disable webhook
- `GET /webhooks/events/types` - List event types

## 🔧 Configuration

### Celery Worker
```bash
celery -A tasks.celery_app.celery worker --loglevel=info
```

### Database Migrations
```bash
# Run migrations
docker exec -it web alembic upgrade head

# Create new migration
docker exec -it web alembic revision --autogenerate -m "description"
```

## 🐛 Troubleshooting

### Upload not working?
1. Check if all Docker containers are running: `docker-compose ps`
2. View worker logs: `docker-compose logs worker`
3. Check if Redis is accessible: `docker exec -it redis redis-cli ping`

### Database connection issues?
1. Check PostgreSQL logs: `docker-compose logs db`
2. Verify connection string in environment variables
3. Ensure database is healthy: `docker-compose ps db`

### Port conflicts?
```bash
# Check what's using port 8000
netstat -ano | findstr :8000

# Kill the process
taskkill /PID <PID> /F
```

## 🚢 Deployment

### Deploy to Render

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://render.com
   - Click "New +" → "Blueprint"
   - Connect your GitHub repository
   - Render will auto-detect `render.yaml`
   - Click "Apply"

3. **Wait for deployment** (~10-15 minutes)
   - PostgreSQL, Redis, Web, and Worker will be created
   - Environment variables are auto-configured

4. **Run database migrations**
   ```bash
   # In Render dashboard, open Shell for web service
   alembic upgrade head
   ```

### Production Considerations

- Enable HTTPS (automatic on Render)
- Set up proper logging and monitoring
- Configure backup strategy for PostgreSQL
- Implement rate limiting for uploads
- Add authentication/authorization
- Set up error tracking (e.g., Sentry)

## 📝 CSV Format

Expected CSV format:
```csv
name,sku,description,price,category,stock_quantity
"Product 1","SKU-001","Description",19.99,"Electronics",100
"Product 2","SKU-002","Description",29.99,"Office",50
```

**Required columns**: `name`, `sku`
**Optional columns**: `description`, `price`, `category`, `stock_quantity`, `image_url`

## 🧪 Testing

### Manual Testing
1. Upload `products.csv` (500K rows)
2. Monitor real-time progress
3. Verify data in Products page
4. Test CRUD operations
5. Configure and test webhooks


## 🙏 Acknowledgments

- FastAPI for the amazing web framework
- Celery for robust task queue
- PostgreSQL for reliable database
- Render for easy deployment
