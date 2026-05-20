from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, func
from sqlalchemy.orm import relationship

from app.database import Base


class RoundQuestionTemplate(Base):
    __tablename__ = "round_question_templates"

    id = Column(Integer, primary_key=True, index=True)

    round_template_id = Column(Integer, ForeignKey("round_templates.id"), nullable=False, index=True)

    question_code = Column(String, nullable=False, index=True)
    sequence_no = Column(Integer, nullable=False, index=True)

    role_code = Column(String, nullable=True, index=True)

    title = Column(String, nullable=True)
    prompt = Column(Text, nullable=False)

    ui_template = Column(String, nullable=False)
    answer_mode = Column(String, nullable=False, index=True)

    auto_check = Column(Boolean, nullable=False, default=True)
    manual_check_allowed = Column(Boolean, nullable=False, default=False)

    allowed_house_keys = Column(Text, nullable=True)

    content_json = Column(Text, nullable=True)
    reward_json = Column(Text, nullable=True)
    fail_effect_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    round_template = relationship("RoundTemplate", back_populates="questions")