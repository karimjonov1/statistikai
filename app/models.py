from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True, nullable=False)
    target_url = Column(String(2048), nullable=False)
    utm_source = Column(String(255), nullable=True)
    utm_medium = Column(String(255), nullable=True)
    utm_campaign = Column(String(255), nullable=True)
    utm_term = Column(String(255), nullable=True)
    utm_content = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    clicks = relationship("Click", back_populates="link", cascade="all, delete-orphan")


class Click(Base):
    __tablename__ = "clicks"
    __table_args__ = (
        Index("ix_clicks_link_id_created_at", "link_id", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(Integer, ForeignKey("links.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    referrer = Column(String(2048), nullable=True)
    user_agent = Column(String(1024), nullable=True)
    ip_address = Column(String(64), nullable=True)

    link = relationship("Link", back_populates="clicks")