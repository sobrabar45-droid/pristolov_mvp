from datetime import datetime, timezone

from sqlalchemy import Column, Integer, ForeignKey, String, Text, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class GameDuel(Base):
    __tablename__ = "game_duels"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    challenger_house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)
    target_house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)

    status = Column(String, nullable=False, default="challenged")
    stake_gold = Column(Integer, nullable=False, default=3)

    winner_house_id = Column(Integer, ForeignKey("houses.id"), nullable=True, index=True)

    refused_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    notes_json = Column(Text, nullable=True)
    challenger_tower_bonus = Column(String, nullable=True)
    target_tower_bonus = Column(String, nullable=True)
    duel_advantage_side = Column(String, nullable=True)
    duel_advantage_class = Column(String, nullable=True)
    duel_advantage_payload_json = Column(Text, nullable=True)
    duel_format = Column(String, nullable=True)
    live_bonus_side = Column(String, nullable=True)
    live_bonus_code = Column(String, nullable=True)
    live_bonus_label = Column(String, nullable=True)
    live_bonus_host_text = Column(Text, nullable=True)
    live_bonus_tv_text = Column(Text, nullable=True)
    live_bonus_payload_json = Column(Text, nullable=True)
    influence_transfer_amount = Column(Integer, nullable=False, default=0)
    bonus_payload_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    game = relationship("Game")
    challenger_house = relationship("House", foreign_keys=[challenger_house_id])
    target_house = relationship("House", foreign_keys=[target_house_id])
    winner_house = relationship("House", foreign_keys=[winner_house_id])
