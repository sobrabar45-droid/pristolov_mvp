from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    room_code = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    template_code = Column(String, nullable=True)
    scenario_id = Column(Integer, nullable=True, index=True)
    scenario_code = Column(String, nullable=True, index=True)

    houses = relationship("House", back_populates="game")
    players = relationship("Player", back_populates="game")
