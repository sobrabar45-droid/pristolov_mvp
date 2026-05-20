from sqlalchemy import Column, Integer, String, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplate(Base):
    __tablename__ = "game_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    description = Column(Text, nullable=True)

    default_team_size_min = Column(Integer, nullable=True)
    default_team_size_max = Column(Integer, nullable=True)

    acts_total = Column(Integer, nullable=True)
    supported_houses_min = Column(Integer, nullable=True)
    supported_houses_max = Column(Integer, nullable=True)
    recommended_houses = Column(Integer, nullable=True)
    simultaneous_houses_supported = Column(Integer, nullable=True)

    allow_role_overlap_in_small_team = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    houses = relationship(
        "GameTemplateHouse",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    roles = relationship(
        "GameTemplateRole",
        back_populates="template",
        cascade="all, delete-orphan",
    )
    acts = relationship(
        "GameTemplateAct",
        back_populates="template",
        cascade="all, delete-orphan",
    )