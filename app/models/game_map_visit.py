from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Text
from sqlalchemy.orm import relationship

from app.database import Base


class GameMapVisit(Base):
    __tablename__ = "game_map_visits"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)
    triggered_by_player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)

    location_code = Column(String, nullable=False, index=True)
    visit_no_for_house = Column(Integer, nullable=False, default=1)

    outcome_type = Column(String, nullable=True)
    outcome_text = Column(Text, nullable=True)

    rolled_outcome_json = Column(Text, nullable=True)
    effect_data_json = Column(Text, nullable=True)
    meta_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    game = relationship("Game")
    house = relationship("House")
    triggered_by_player = relationship("Player")