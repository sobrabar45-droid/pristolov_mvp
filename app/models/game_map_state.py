from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class GameMapState(Base):
    __tablename__ = "game_map_states"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)

    current_location_code = Column(String, nullable=True)

    moves_total = Column(Integer, nullable=False, default=0)
    moves_used = Column(Integer, nullable=False, default=0)

    active_location_codes = Column(Text, nullable=True)
    opened_tags = Column(Text, nullable=True)
    session_modifiers = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    game = relationship("Game")
    house = relationship("House")

    __table_args__ = (
        UniqueConstraint("game_id", "house_id", name="uq_game_map_state_game_house"),
    )