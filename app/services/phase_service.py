from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.game_phase import GamePhase
from app.models.game_host_round import GameHostRound
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.game_assignment import GameAssignment


def has_active_phase(db: Session, game_id: int, phase_type: str) -> bool:
    phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.phase_type == phase_type,
            GamePhase.status == "active",
        )
        .first()
    )
    return phase is not None


def has_any_active_phase(db: Session, game_id: int, phase_types: list[str]) -> bool:
    if not isinstance(phase_types, list) or not phase_types:
        return False

    normalized_phase_types = [
        str(phase_type).strip()
        for phase_type in phase_types
        if isinstance(phase_type, str) and phase_type.strip()
    ]

    if not normalized_phase_types:
        return False

    phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.phase_type.in_(normalized_phase_types),
            GamePhase.status == "active",
        )
        .first()
    )
    return phase is not None


def open_game_phase_logic(db: Session, room_code: str, phase_type: str):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    existing_phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == phase_type,
            GamePhase.status == "active",
        )
        .first()
    )

    if existing_phase:
        return {
            "ok": False,
            "message": f'Фаза "{phase_type}" уже активна',
            "phase": {
                "id": existing_phase.id,
                "game_id": existing_phase.game_id,
                "phase_type": existing_phase.phase_type,
                "status": existing_phase.status,
                "opened_at": existing_phase.opened_at.isoformat() if existing_phase.opened_at else None,
                "closed_at": existing_phase.closed_at.isoformat() if existing_phase.closed_at else None,
                "payload": existing_phase.payload,
            },
        }

    phase = GamePhase(
        game_id=game.id,
        phase_type=phase_type,
        status="active",
        payload=None,
    )

    db.add(phase)
    db.flush()

    return {
        "ok": True,
        "message": f'Фаза "{phase_type}" открыта',
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "phase": {
            "id": phase.id,
            "game_id": phase.game_id,
            "phase_type": phase.phase_type,
            "status": phase.status,
            "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
            "closed_at": phase.closed_at.isoformat() if phase.closed_at else None,
            "payload": phase.payload,
        },
    }


def close_game_phase_logic(db: Session, room_code: str, phase_type: str):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == phase_type,
            GamePhase.status == "active",
        )
        .first()
    )

    if not phase:
        return {
            "ok": False,
            "message": f'Активная фаза "{phase_type}" не найдена',
            "room_code": room_code,
        }

    auto_closed_host_round_ids = []
    auto_resolved_question_ids = []
    expired_assignment_ids = []

    if phase_type == "host_round":
        active_host_rounds = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == game.id,
                GameHostRound.status == "active",
            )
            .all()
        )

        for host_round in active_host_rounds:
            active_questions = (
                db.query(GameHostRoundQuestion)
                .filter(
                    GameHostRoundQuestion.host_round_id == host_round.id,
                    GameHostRoundQuestion.status == "active",
                )
                .all()
            )

            for question in active_questions:
                question.status = "resolved"
                question.answers_open = False
                question.resolved_at = datetime.now(timezone.utc)
                auto_resolved_question_ids.append(question.id)

                related_assignments = (
                    db.query(GameAssignment)
                    .filter(GameAssignment.host_round_question_id == question.id)
                    .all()
                )

                for assignment in related_assignments:
                    if assignment.status == "issued":
                        assignment.status = "expired"
                        if assignment.id not in expired_assignment_ids:
                            expired_assignment_ids.append(assignment.id)

            remaining_assignments = (
                db.query(GameAssignment)
                .filter(
                    GameAssignment.host_round_id == host_round.id,
                    GameAssignment.status == "issued",
                )
                .all()
            )

            for assignment in remaining_assignments:
                assignment.status = "expired"
                if assignment.id not in expired_assignment_ids:
                    expired_assignment_ids.append(assignment.id)

            host_round.answers_open = False
            host_round.status = "finished"
            auto_closed_host_round_ids.append(host_round.id)

    phase.status = "closed"
    phase.closed_at = datetime.now(timezone.utc)

    return {
        "ok": True,
        "message": f'Фаза "{phase_type}" закрыта',
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "phase": {
            "id": phase.id,
            "game_id": phase.game_id,
            "phase_type": phase.phase_type,
            "status": phase.status,
            "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
            "closed_at": phase.closed_at.isoformat() if phase.closed_at else None,
            "payload": phase.payload,
        },
        "host_round_cleanup": {
            "applied": phase_type == "host_round",
            "auto_closed_host_round_ids": auto_closed_host_round_ids,
            "auto_resolved_question_ids": auto_resolved_question_ids,
            "expired_assignment_ids": expired_assignment_ids,
        },
    }


def get_game_phases_logic(db: Session, room_code: str):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    phases = (
        db.query(GamePhase)
        .filter(GamePhase.game_id == game.id)
        .order_by(GamePhase.id.asc())
        .all()
    )

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "phases_count": len(phases),
        "phases": [
            {
                "id": phase.id,
                "game_id": phase.game_id,
                "phase_type": phase.phase_type,
                "status": phase.status,
                "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
                "closed_at": phase.closed_at.isoformat() if phase.closed_at else None,
                "payload": phase.payload,
            }
            for phase in phases
        ],
    }


def can_use_diplomacy_logic(db: Session, room_code: str):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    diplomacy_active = has_active_phase(db, game.id, "diplomacy")

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "can_use_diplomacy": diplomacy_active,
        "reason": "Фаза diplomacy активна" if diplomacy_active else "Фаза diplomacy не активна",
    }


def can_use_map_logic(db: Session, room_code: str):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    allowed_phase_types = ["map", "free_play"]
    map_active = has_any_active_phase(db, game.id, allowed_phase_types)

    active_allowed_phases = [
        phase_type
        for phase_type in allowed_phase_types
        if has_active_phase(db, game.id, phase_type)
    ]

    if map_active:
        reason = "Активна одна из разрешающих фаз карты: " + ", ".join(active_allowed_phases)
    else:
        reason = "Ни одна из фаз карты не активна. Нужна phase_type: map или free_play"

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "can_use_map": map_active,
        "allowed_phase_types": allowed_phase_types,
        "active_allowed_phases": active_allowed_phases,
        "reason": reason,
    }

def is_phase_active(db: Session, game_id: int, phase_type: str) -> bool:
    phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.phase_type == phase_type,
            GamePhase.status == "active",
        )
        .first()
    )
    return phase is not None
