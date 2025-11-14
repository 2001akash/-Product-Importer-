# Minimal placeholder - run `alembic init` locally for a proper setup.
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os

config = context.config
fileConfig(config.config_file_name)

from app.database import Base
from app import models

target_metadata = Base.metadata

def run_migrations_offline():
    pass

def run_migrations_online():
    pass

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
