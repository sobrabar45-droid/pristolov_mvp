from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class GameHouseTower(Base):
    __tablename__ = "game_house_towers"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="draft")
    levels_count = Column(Integer, nullable=False, default=0)
    has_foundation = Column(Boolean, nullable=False, default=False)
    unique_element_count = Column(Integer, nullable=False, default=0)

    blueprint_code = Column(String, nullable=True)
    blueprint_applied = Column(Boolean, nullable=False, default=False)
    tower_score = Column(Integer, nullable=False, default=0)

    parts_json = Column(Text, nullable=True)
    notes_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    game = relationship("Game")
    house = relationship("House")

    __table_args__ = (
        UniqueConstraint("game_id", "house_id", name="uq_game_house_tower_game_house"),
    )
