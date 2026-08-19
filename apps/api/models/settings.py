from sqlalchemy import Column, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class CollectionSettings(Base):
    __tablename__ = "collection_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    is_paused = Column(Boolean, nullable=False, default=False)

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
