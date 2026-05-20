from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class House(Base):
    __tablename__ = "houses"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    house_key = Column(String, nullable=False)
    name = Column(String, nullable=False)
    motto = Column(String, nullable=True)
    color = Column(String, nullable=True)

    team_size_declared = Column(Integer, nullable=True)
    invite_code = Column(String, nullable=True, unique=True, index=True)
    entry_mode = Column(String, nullable=True)
    leader_player_id = Column(Integer, nullable=True)
    is_ready = Column(Boolean, nullable=False, default=False)

    resource_gold = Column(Integer, nullable=False, default=0)
    resource_influence = Column(Integer, nullable=False, default=0)
    resource_stone = Column(Integer, nullable=False, default=0)
    resource_wood = Column(Integer, nullable=False, default=0)
    resource_iron = Column(Integer, nullable=False, default=0)
    resource_scroll = Column(Integer, nullable=False, default=0)
    resource_key = Column(Integer, nullable=False, default=0)
    resource_fire = Column(Integer, nullable=False, default=0)

    fate_bias = Column(Integer, nullable=False, default=0)

    game = relationship("Game", back_populates="houses")
    players = relationship("Player", back_populates="house")
