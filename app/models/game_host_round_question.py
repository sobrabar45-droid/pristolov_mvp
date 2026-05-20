from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameHostRoundQuestion(Base):
    __tablename__ = "game_host_round_questions"

    id = Column(Integer, primary_key=True, index=True)

    host_round_id = Column(Integer, ForeignKey("game_host_rounds.id"), nullable=False, index=True)
    question_template_id = Column(Integer, ForeignKey("round_question_templates.id"), nullable=False, index=True)

    sequence_no = Column(Integer, nullable=False, index=True)

    status = Column(String, nullable=False, default="draft", index=True)  # draft / active / checking / resolved / closed
    answers_open = Column(Boolean, nullable=False, default=False)

    check_mode = Column(String, nullable=False, default="auto", index=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    host_round = relationship("GameHostRound", foreign_keys=[host_round_id])
    question_template = relationship("RoundQuestionTemplate", foreign_keys=[question_template_id])