from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateRole(Base):
    __tablename__ = "game_template_roles"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)

    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    ui_track = Column(String, nullable=True)
    assignment_types = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate", back_populates="roles")