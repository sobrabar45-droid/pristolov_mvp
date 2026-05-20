from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateAct(Base):
    __tablename__ = "game_template_acts"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)

    act_number = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    enabled_assignment_types = Column(Text, nullable=True)
    event_tags = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate", back_populates="acts")