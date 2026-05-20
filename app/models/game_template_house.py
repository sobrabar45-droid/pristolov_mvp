from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateHouse(Base):
    __tablename__ = "game_template_houses"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)

    house_key = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    theme_tags = Column(Text, nullable=True)

    diplomat_bias = Column(Text, nullable=True)
    maester_bias = Column(Text, nullable=True)
    whisper_bias = Column(Text, nullable=True)
    treasurer_bias = Column(Text, nullable=True)
    lord_bias = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate", back_populates="houses")