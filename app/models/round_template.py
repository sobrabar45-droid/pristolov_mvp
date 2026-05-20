from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class RoundTemplate(Base):
    __tablename__ = "round_templates"

    id = Column(Integer, primary_key=True, index=True)

    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)
    scenario_id = Column(Integer, ForeignKey("game_scenario_templates.id"), nullable=True, index=True)

    round_code = Column(String, nullable=False, index=True)
    import_key = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)

    order_no = Column(Integer, nullable=True, index=True)
    act_number = Column(Integer, nullable=False, index=True)
    round_type = Column(String, nullable=True, index=True)
    round_kind = Column(String, nullable=False, index=True)
    check_mode = Column(String, nullable=False, default="auto", index=True)

    questions_total = Column(Integer, nullable=False, default=1)
    time_limit_sec = Column(Integer, nullable=True)

    is_host_led = Column(Boolean, nullable=False, default=True)
    is_optional = Column(Boolean, nullable=False, default=False)
    bar_window_opens = Column(Boolean, nullable=False, default=False)

    scoring_mode = Column(String, nullable=True)

    question_transition_mode = Column(String, nullable=False, default="manual")
    round_transition_mode = Column(String, nullable=False, default="manual")

    intro_text = Column(Text, nullable=True)
    outro_text = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate")
    scenario = relationship("GameScenarioTemplate", back_populates="rounds")
    questions = relationship(
        "RoundQuestionTemplate",
        back_populates="round_template",
        cascade="all, delete-orphan"
    )
