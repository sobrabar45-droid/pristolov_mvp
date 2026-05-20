from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base


class GameDeal(Base):
    __tablename__ = "game_deals"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    from_house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)
    to_house_id = Column(Integer, ForeignKey("houses.id"), nullable=False)

    # 🔗 связь с родительской сделкой (для counter-offer)
    parent_deal_id = Column(Integer, ForeignKey("game_deals.id"), nullable=True)

    status = Column(String, default="pending", nullable=False)
    # pending / accepted / declined / cancelled / countered

    offer = Column(JSON, nullable=True)
    note = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)

    # relationships
    game = relationship("Game")

    from_house = relationship(
        "House",
        foreign_keys=[from_house_id]
    )

    to_house = relationship(
        "House",
        foreign_keys=[to_house_id]
    )

    # 🔗 (опционально, но лучше сразу правильно)
    parent_deal = relationship(
        "GameDeal",
        remote_side=[id],
        uselist=False
    )