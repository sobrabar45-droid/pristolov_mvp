from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class HouseGoldTransaction(Base):
    __tablename__ = "house_gold_transactions"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)

    # Сколько изменили золота:
    # +6 = начислили
    # -3 = списали
    amount = Column(Integer, nullable=False)

    # Снимок баланса до и после операции
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # Тип операции: grant_check / spend_action / pvp_win и т.д.
    operation_type = Column(String(50), nullable=False, index=True)

    # Источник: check / expedition / pvp_duel / manual / house_setup
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(Integer, nullable=True, index=True)

    # Человеческое объяснение
    reason = Column(String(255), nullable=False)
    comment = Column(Text, nullable=True)

    # Кто инициировал / подтвердил
    performed_by_player_id = Column(Integer, ForeignKey("players.id"), nullable=True)

    # Второй дом, если это PvP или перевод между домами
    counterparty_house_id = Column(Integer, ForeignKey("houses.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    game = relationship("Game", foreign_keys=[game_id])
    house = relationship("House", foreign_keys=[house_id])
    performed_by_player = relationship("Player", foreign_keys=[performed_by_player_id])
    counterparty_house = relationship("House", foreign_keys=[counterparty_house_id])