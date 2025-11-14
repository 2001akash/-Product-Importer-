# Acme Product Importer — Scaffold

This repository is a ready-to-run scaffold for the Acme product importer assignment.

## Features
- Upload large CSV (saved and processed asynchronously)
- Real-time progress via WebSocket + Redis pub/sub
- Fast ingestion using `COPY` to a temp table and single upsert
- Product CRUD with filtering and pagination
- Webhook CRUD + test trigger
- Bulk delete endpoint

## Quick local run (dev)

1. Copy `.env.example` to `.env` and edit if needed.
2. Build and start services:

```bash
docker-compose up --build
