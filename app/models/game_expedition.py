from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index, text
from sqlalchemy.orm import relationship

from app.database import Base


class GameExpedition(Base):
    __tablename__ = "game_expeditions"
    __table_args__ = (
        Index(
            "uq_active_expedition_per_house",
            "game_id",
            "house_id",
            unique=True,
            postgresql_where=text("status IN ('planned', 'approved')"),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=False, index=True)
    phase_id = Column(Integer, ForeignKey("game_phases.id"), nullable=True, index=True)

    status = Column(String, nullable=False, default="planned")  # planned / approved / resolved
    target_location_code = Column(String, nullable=True)
    leader_player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)
    approved_by_player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True, default=None)

    game = relationship("Game")
    house = relationship("House")
    phase = relationship("GamePhase")
    leader_player = relationship("Player", foreign_keys=[leader_player_id])
    approved_by_player = relationship("Player", foreign_keys=[approved_by_player_id])
    members = relationship(
        "GameExpeditionMember",
        back_populates="expedition",
        cascade="all, delete-orphan",
    )


class GameExpeditionMember(Base):
    __tablename__ = "game_expedition_members"

    id = Column(Integer, primary_key=True, index=True)

    expedition_id = Column(Integer, ForeignKey("game_expeditions.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)

    expedition = relationship("GameExpedition", back_populates="members")
    player = relationship("Player")
