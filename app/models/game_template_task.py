from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateTask(Base):
    __tablename__ = "game_template_tasks"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)
    pool_id = Column(Integer, ForeignKey("game_template_task_pools.id"), nullable=False, index=True)

    task_code = Column(String, nullable=False, index=True)
    role_code = Column(String, nullable=False, index=True)
    assignment_type = Column(String, nullable=False, index=True)

    title = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    ui_template = Column(String, nullable=True)

    difficulty = Column(Integer, nullable=True)
    act_min = Column(Integer, nullable=True)
    act_max = Column(Integer, nullable=True)

    allowed_house_keys = Column(Text, nullable=True)
    content_json = Column(Text, nullable=True)
    reward_json = Column(Text, nullable=True)
    fail_effect_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate")
    pool = relationship("GameTemplateTaskPool")