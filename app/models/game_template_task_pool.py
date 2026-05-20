from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateTaskPool(Base):
    __tablename__ = "game_template_task_pools"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)

    pool_code = Column(String, nullable=False, index=True)
    role_code = Column(String, nullable=False, index=True)
    assignment_type = Column(String, nullable=False, index=True)
    selection_policy = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate")