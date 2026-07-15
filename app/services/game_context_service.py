from sqlalchemy.orm import Session

from app.models.game_template import GameTemplate
from app.models.round_template import RoundTemplate


def resolve_template_for_game(db: Session, game):
    template_code = getattr(game, "template_code", None)

    if template_code:
        template = (
            db.query(GameTemplate)
            .filter(GameTemplate.template_code == template_code)
            .first()
        )
        if template:
            return {
                "ok": True,
                "template": template,
            }

    templates = db.query(GameTemplate).order_by(GameTemplate.id.asc()).all()

    if len(templates) == 1:
        return {
            "ok": True,
            "template": templates[0],
            "fallback_used": True,
        }

    if len(templates) == 0:
        return {
            "ok": False,
            "message": "В БД нет ни одного импортированного шаблона",
        }

    return {
        "ok": False,
        "message": "У игры нет template_code, а в БД несколько шаблонов. Нужна явная привязка игры к шаблону.",
    }


def resolve_round_template_for_game(
    db: Session,
    game,
    round_code: str,
    *,
    round_template_id: int | None = None,
    scenario_id: int | None = None,
):
    template_resolution = resolve_template_for_game(db, game)
    if not template_resolution.get("ok"):
        return template_resolution

    template = template_resolution["template"]

    round_query = (
        db.query(RoundTemplate)
        .filter(
            RoundTemplate.template_id == template.id,
            RoundTemplate.round_code == round_code,
        )
    )

    if round_template_id is not None:
        round_query = round_query.filter(RoundTemplate.id == round_template_id)

    if scenario_id is not None:
        round_query = round_query.filter(RoundTemplate.scenario_id == scenario_id)

    round_template = round_query.first()

    if not round_template:
        return {
            "ok": False,
            "message": f'Раунд "{round_code}" не найден в шаблоне "{template.template_code}"',
            "round_code": round_code,
            "template_code": template.template_code,
        }

    if round_template_id is not None and round_template.id != round_template_id:
        return {
            "ok": False,
            "message": "Resolved round template does not match the scenario-selected round template",
            "round_code": round_code,
            "expected_round_template_id": round_template_id,
            "resolved_round_template_id": round_template.id,
        }

    if scenario_id is not None and round_template.scenario_id != scenario_id:
        return {
            "ok": False,
            "message": "Resolved round template does not belong to the linked scenario",
            "round_code": round_code,
            "expected_scenario_id": scenario_id,
            "resolved_scenario_id": round_template.scenario_id,
        }

    return {
        "ok": True,
        "template": template,
        "round_template": round_template,
        "template_fallback_used": template_resolution.get("fallback_used", False),
    }
