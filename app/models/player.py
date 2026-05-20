from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=True, index=True)

    nickname = Column(String, nullable=False)

    # Новый личный токен игрока для входа в player API
    player_token = Column(String(64), unique=True, index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    game = relationship("Game", back_populates="players")
    house = relationship("House", back_populates="players")
    role = relationship("Role")
    assignments = relationship("GameAssignment", back_populates="player")