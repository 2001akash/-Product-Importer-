from sqlalchemy import Column, BigInteger, Text, Numeric, Boolean, TIMESTAMP, func
from sqlalchemy.sql import expression
from .database import Base

class Product(Base):
    __tablename__ = 'products'
    id = Column(BigInteger, primary_key=True)
    sku = Column(Text, nullable=False)
    name = Column(Text)
    description = Column(Text)
    price = Column(Numeric(12,2))
    active = Column(Boolean, server_default=expression.true(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

class Webhook(Base):
    __tablename__ = 'webhooks'
    id = Column(BigInteger, primary_key=True)
    url = Column(Text, nullable=False)
    event_types = Column(Text)
    enabled = Column(Boolean, server_default=expression.true(), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
