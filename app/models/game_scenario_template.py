from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameScenarioTemplate(Base):
    __tablename__ = "game_scenario_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=True, index=True)

    code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String, nullable=False, default="draft", index=True)
    recommended_houses = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    template = relationship("GameTemplate")
    rounds = relationship("RoundTemplate", back_populates="scenario")
