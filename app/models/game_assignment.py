from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class GameAssignment(Base):
    __tablename__ = "game_assignments"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    house_id = Column(Integer, ForeignKey("houses.id"), nullable=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)

    host_round_id = Column(Integer, ForeignKey("game_host_rounds.id"), nullable=True, index=True)
    host_round_question_id = Column(Integer, ForeignKey("game_host_round_questions.id"), nullable=True, index=True)

    template_pool_id = Column(Integer, ForeignKey("game_template_task_pools.id"), nullable=True)
    template_task_id = Column(Integer, ForeignKey("game_template_tasks.id"), nullable=True)

    role_code = Column(String, nullable=True)
    delivery_mode = Column(String, nullable=True)
    answer_mode = Column(String, nullable=True)

    auto_check = Column(Boolean, nullable=False, default=False)
    status = Column(String, nullable=False, default="issued")
    is_correct = Column(Boolean, nullable=True)
    result_applied = Column(Boolean, nullable=False, default=False)
    triggered_by_host = Column(Boolean, nullable=False, default=False)

    answered_by_player_id = Column(Integer, nullable=True)
    answer_payload = Column(Text, nullable=True)
    result_payload = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    player = relationship("Player", back_populates="assignments")
    template_task = relationship("GameTemplateTask")
    host_round = relationship("GameHostRound")
    host_round_question = relationship("GameHostRoundQuestion")