from app.database import Base

from .game import Game
from .house import House
from .player import Player
from .role import Role

from .game_template import GameTemplate
from .game_template_house import GameTemplateHouse
from .game_template_role import GameTemplateRole
from .game_template_act import GameTemplateAct
from .game_template_map_node import GameTemplateMapNode
from .game_template_task_pool import GameTemplateTaskPool
from .game_template_task import GameTemplateTask

from .game_assignment import GameAssignment
from .game_host_round import GameHostRound
from .game_host_round_question import GameHostRoundQuestion

from .round_template import RoundTemplate
from .round_question_template import RoundQuestionTemplate
from .game_scenario_template import GameScenarioTemplate

from .game_phase import GamePhase
from .game_deal import GameDeal
from .game_duel import GameDuel
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.game_map_state import GameMapState
from app.models.game_map_visit import GameMapVisit
from .game_house_tower import GameHouseTower

# 👇 ВОТ ЭТО ДОБАВИЛИ (КРИТИЧНО)
from .game_expedition import GameExpedition, GameExpeditionMember
