from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class GamePhase(Base):
    __tablename__ = "game_phases"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)

    phase_type = Column(String, nullable=False)
    status = Column(String, default="active")

    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    payload = Column(JSON, nullable=True)

    game = relationship("Game", backref="phases")