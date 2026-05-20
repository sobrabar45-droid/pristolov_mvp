from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class GameTemplateMapNode(Base):
    __tablename__ = "game_template_map_nodes"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("game_templates.id"), nullable=False, index=True)

    node_code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    node_type = Column(String, nullable=True)

    visible_for_roles = Column(Text, nullable=True)
    visible_for_houses = Column(Text, nullable=True)

    act_min = Column(Integer, nullable=True)
    act_max = Column(Integer, nullable=True)
    move_cost = Column(Integer, nullable=True)

    result_mode = Column(String, nullable=True)
    payload = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("GameTemplate")