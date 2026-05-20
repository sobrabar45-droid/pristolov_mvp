from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.game_expedition import GameExpedition, GameExpeditionMember
from app.models.game_phase import GamePhase
from app.models.player import Player
from app.models.role import Role


def ensure_expedition_schema(engine):
    statements = [
        "ALTER TABLE game_expeditions ADD COLUMN IF NOT EXISTS phase_id INTEGER NULL",
        "ALTER TABLE game_expeditions ADD COLUMN IF NOT EXISTS leader_player_id INTEGER",
        "ALTER TABLE game_expeditions ADD COLUMN IF NOT EXISTS approved_by_player_id INTEGER",
        "ALTER TABLE game_expeditions ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ NULL",
        "CREATE INDEX IF NOT EXISTS ix_game_expeditions_phase_id ON game_expeditions(phase_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_expeditions_leader_player_id ON game_expeditions(leader_player_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_expeditions_approved_by_player_id ON game_expeditions(approved_by_player_id)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def validate_expedition_creation(db: Session, *, game_id: int, house_id: int):
    active_phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.status == "active",
            GamePhase.phase_type.in_(["map", "free_play"]),
        )
        .order_by(GamePhase.opened_at.desc(), GamePhase.id.desc())
        .first()
    )

    if not active_phase:
        return {
            "ok": False,
            "message": "Экспедиции доступны только на этапе карты",
        }

    active_expedition = (
        db.query(GameExpedition)
        .filter(
            GameExpedition.game_id == game_id,
            GameExpedition.house_id == house_id,
            GameExpedition.status.in_(["planned", "approved"]),
        )
        .first()
    )

    if active_expedition:
        return {
            "ok": False,
            "message": "У Дома уже есть активная экспедиция",
            "expedition_id": active_expedition.id,
            "status": active_expedition.status,
        }

    used_this_phase = (
        db.query(GameExpedition)
        .filter(
            GameExpedition.game_id == game_id,
            GameExpedition.house_id == house_id,
            GameExpedition.phase_id == active_phase.id,
            GameExpedition.status.in_(["planned", "approved", "resolved"]),
        )
        .first()
    )

    if used_this_phase:
        return {
            "ok": False,
            "message": "Дом уже использовал экспедицию на этом этапе",
            "expedition_id": used_this_phase.id,
            "status": used_this_phase.status,
        }

    return None


def create_expedition(db: Session, *, game_id: int, house_id: int) -> GameExpedition:
    blocked = validate_expedition_creation(db, game_id=game_id, house_id=house_id)
    if blocked:
        return blocked

    active_phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.status == "active",
            GamePhase.phase_type.in_(["map", "free_play"]),
        )
        .order_by(GamePhase.opened_at.desc(), GamePhase.id.desc())
        .first()
    )

    if not active_phase:
        return {
            "ok": False,
            "message": "Экспедиции доступны только на этапе карты",
        }

    try:
        expedition = GameExpedition(
            game_id=game_id,
            house_id=house_id,
            phase_id=active_phase.id,
            status="planned",
        )
        db.add(expedition)
        db.flush()
        return expedition
    except IntegrityError:
        db.rollback()
        active_expedition = (
            db.query(GameExpedition)
            .filter(
                GameExpedition.game_id == game_id,
                GameExpedition.house_id == house_id,
                GameExpedition.status.in_(["planned", "approved"]),
            )
            .first()
        )
        return {
            "ok": False,
            "message": "У Дома уже есть активная экспедиция",
            "expedition_id": active_expedition.id if active_expedition else None,
            "status": active_expedition.status if active_expedition else None,
        }


def add_member(db: Session, *, expedition_id: int, player_id: int) -> GameExpeditionMember:
    expedition = (
        db.query(GameExpedition)
        .filter(GameExpedition.id == expedition_id)
        .first()
    )

    if not expedition:
        raise ValueError("Экспедиция не найдена")

    existing = (
        db.query(GameExpeditionMember)
        .filter(
            GameExpeditionMember.expedition_id == expedition_id,
            GameExpeditionMember.player_id == player_id,
        )
        .first()
    )
    if existing:
        return existing

    if expedition.approved_by_player_id is not None or expedition.approved_at is not None:
        expedition.approved_by_player_id = None
        expedition.approved_at = None
        expedition.status = "planned"

    member = GameExpeditionMember(
        expedition_id=expedition_id,
        player_id=player_id,
    )
    db.add(member)
    db.flush()
    return member


def get_expedition_roles(db: Session, expedition_id: int) -> list[str]:
    members = (
        db.query(GameExpeditionMember)
        .filter(GameExpeditionMember.expedition_id == expedition_id)
        .all()
    )

    role_codes: list[str] = []

    for member in members:
        player = db.query(Player).filter(Player.id == member.player_id).first()
        if player and player.role and player.role.code:
            role_codes.append(player.role.code)

    unique_codes: list[str] = []
    seen = set()

    for code in role_codes:
        if code not in seen:
            unique_codes.append(code)
            seen.add(code)

    return unique_codes


def get_expedition_members(db: Session, expedition_id: int) -> list[GameExpeditionMember]:
    return (
        db.query(GameExpeditionMember)
        .filter(GameExpeditionMember.expedition_id == expedition_id)
        .order_by(GameExpeditionMember.id.asc())
        .all()
    )


def get_house_lord_player(db: Session, *, game_id: int, house_id: int) -> Player | None:
    return (
        db.query(Player)
        .join(Role, Player.role_id == Role.id)
        .filter(
            Player.game_id == game_id,
            Player.house_id == house_id,
            Role.code == "lord_lady",
        )
        .first()
    )


def get_expedition_runtime_context(db: Session, expedition: GameExpedition) -> dict:
    members = get_expedition_members(db, expedition.id)
    role_codes = get_expedition_roles(db, expedition.id)
    members_count = len(members)

    lord_player = get_house_lord_player(
        db,
        game_id=expedition.game_id,
        house_id=expedition.house_id,
    )

    approved = expedition.approved_by_player_id is not None and expedition.approved_at is not None
    requires_lord_approval = lord_player is not None
    fallback_without_lord = lord_player is None
    can_depart = approved or fallback_without_lord

    return {
        "members": members,
        "member_ids": [member.player_id for member in members],
        "members_count": members_count,
        "role_codes": role_codes,
        "lord_player_id": lord_player.id if lord_player else None,
        "requires_lord_approval": requires_lord_approval,
        "fallback_without_lord": fallback_without_lord,
        "approved": approved,
        "can_depart": can_depart,
        "approved_by_player_id": expedition.approved_by_player_id,
        "approved_at": expedition.approved_at.isoformat() if expedition.approved_at else None,
        "leader_player_id": expedition.leader_player_id,
        "status": expedition.status,
    }


def approve_expedition(
    db: Session,
    *,
    expedition: GameExpedition,
    player_id: int,
) -> dict:
    player = (
        db.query(Player)
        .join(Role, Player.role_id == Role.id)
        .filter(Player.id == player_id)
        .first()
    )

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден",
            "player_id": player_id,
        }

    if player.game_id != expedition.game_id:
        return {
            "ok": False,
            "message": "Игрок не принадлежит игре этой экспедиции",
            "player_id": player_id,
            "player_game_id": player.game_id,
            "expedition_game_id": expedition.game_id,
        }

    if player.house_id != expedition.house_id:
        return {
            "ok": False,
            "message": "Игрок не принадлежит дому этой экспедиции",
            "player_id": player_id,
            "player_house_id": player.house_id,
            "expedition_house_id": expedition.house_id,
        }

    if not player.role or player.role.code != "lord_lady":
        return {
            "ok": False,
            "message": "Утверждать экспедицию может только Лорд / Леди",
            "player_id": player_id,
            "role_code": player.role.code if player.role else None,
        }

    expedition.leader_player_id = player.id
    expedition.approved_by_player_id = player.id
    expedition.approved_at = datetime.now(timezone.utc)
    expedition.status = "approved"
    db.flush()

    return {
        "ok": True,
        "message": "Экспедиция утверждена Лордом / Леди",
        "expedition": expedition,
        "approved_by": player,
        "expedition_debug": get_expedition_runtime_context(db, expedition),
    }
