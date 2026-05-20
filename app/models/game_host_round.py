from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameHostRound(Base):
    __tablename__ = "game_host_rounds"

    id = Column(Integer, primary_key=True, index=True)

    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)

    template_pool_id = Column(Integer, ForeignKey("game_template_task_pools.id"), nullable=True, index=True)
    template_task_id = Column(Integer, ForeignKey("game_template_tasks.id"), nullable=True, index=True)

    round_template_id = Column(Integer, ForeignKey("round_templates.id"), nullable=True, index=True)

    round_code = Column(String, nullable=True, index=True)
    act_number = Column(Integer, nullable=True, index=True)
    round_kind = Column(String, nullable=True, index=True)

    role_code = Column(String, nullable=False, index=True)

    title = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    ui_template = Column(String, nullable=True)

    questions_total = Column(Integer, nullable=False, default=1)
    current_question_no = Column(Integer, nullable=False, default=1)

    answers_open = Column(Boolean, nullable=False, default=False)
    intro_shown = Column(Boolean, nullable=False, default=False)
    outro_shown = Column(Boolean, nullable=False, default=False)

    status = Column(String, nullable=False, default="active", index=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game")
    round_template = relationship("RoundTemplate", foreign_keys=[round_template_id])