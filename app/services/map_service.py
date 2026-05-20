from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.house import House
from app.services.resource_service import apply_house_effect
from app.services.serialization_utils import load_yaml_file


def load_locations_catalog(locations_file_path: Path) -> dict[str, dict[str, Any]]:
    """
    Загружает YAML-каталог локаций и возвращает словарь:
    {
        "old_market": {...},
        "archive": {...},
    }
    """
    raw = load_yaml_file(locations_file_path)

    if not isinstance(raw, dict):
        raise ValueError("Файл локаций должен содержать объект верхнего уровня")

    locations = raw.get("locations")
    if not isinstance(locations, list):
        raise ValueError('Файл локаций должен содержать ключ "locations" со списком')

    catalog: dict[str, dict[str, Any]] = {}

    for item in locations:
        if not isinstance(item, dict):
            continue

        code = item.get("code")
        if not code or not isinstance(code, str):
            raise ValueError("У локации отсутствует корректный code")

        if code in catalog:
            raise ValueError(f'Дублируется код локации "{code}"')

        catalog[code] = item

    return catalog


def get_location_by_code(catalog: dict[str, dict[str, Any]], location_code: str) -> dict[str, Any]:
    location = catalog.get(location_code)
    if not location:
        raise ValueError(f'Локация "{location_code}" не найдена в каталоге')
    return location


def location_is_available_for_house(
    location: dict[str, Any],
    *,
    house_tags: list[str] | None = None,
) -> tuple[bool, str | None]:
    """
    Проверяет, доступна ли локация дому по тегам доступа.
    Сейчас поддерживаем базовое правило:
    - если у локации нет requires_any_tag -> доступна
    - если есть requires_any_tag -> нужен хотя бы один тег
    """
    required_tags = location.get("requires_any_tag", [])
    house_tags = house_tags or []

    if not required_tags:
        return True, None

    if not isinstance(required_tags, list):
        return False, 'Поле "requires_any_tag" должно быть списком'

    for tag in required_tags:
        if tag in house_tags:
            return True, None

    return False, "Для доступа к этой локации не хватает нужного тега"


def choose_active_locations(
    catalog: dict[str, dict[str, Any]],
    *,
    open_codes: list[str] | None = None,
    base_open_count: int = 4,
    seed: int | None = None,
) -> list[dict[str, Any]]:
    """
    Возвращает активные локации на сессию.
    Если open_codes переданы — берём их жёстко.
    Иначе выбираем случайно base_open_count штук из каталога.
    """
    if open_codes:
        result = []
        for code in open_codes:
            result.append(get_location_by_code(catalog, code))
        return result

    all_locations = list(catalog.values())
    if base_open_count <= 0:
        return []

    if len(all_locations) <= base_open_count:
        return all_locations

    rng = random.Random(seed)
    return rng.sample(all_locations, base_open_count)


def apply_repeat_penalty_to_outcomes(
    outcomes: list[dict[str, Any]],
    *,
    visit_count: int,
    repeat_penalty: int,
) -> list[dict[str, Any]]:
    """
    Антиабуз:
    - penalty применяется со 2-го визита
    - reward/mixed/hidden постепенно проседают
    - empty/penalty/ambush слегка растут
    """
    if visit_count <= 0:
        return deepcopy(outcomes)

    adjusted = deepcopy(outcomes)

    degradation_steps = max(0, visit_count - 1)
    penalty_total = repeat_penalty * degradation_steps

    for outcome in adjusted:
        base_weight = outcome.get("weight", 0)
        outcome_type = outcome.get("type")

        if not isinstance(base_weight, int):
            continue

        if outcome_type in {"reward", "mixed", "hidden"}:
            new_weight = base_weight - penalty_total
            outcome["weight"] = max(1, new_weight)

        elif outcome_type in {"empty", "penalty", "ambush"}:
            new_weight = base_weight + penalty_total
            outcome["weight"] = max(1, new_weight)

        else:
            outcome["weight"] = max(1, base_weight)

    return adjusted


def apply_role_modifiers_to_outcomes(
    location: dict[str, Any],
    outcomes: list[dict[str, Any]],
    *,
    roles: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Если среди expedition roles есть preferred role этой локации:
    - reward/mixed/hidden немного усиливаются
    - empty/penalty/ambush немного ослабляются
    """
    roles = roles or []
    preferred_roles = location.get("preferred_roles", [])

    if not isinstance(preferred_roles, list) or not preferred_roles:
        return deepcopy(outcomes)

    has_preferred_role = any(role in preferred_roles for role in roles)
    if not has_preferred_role:
        return deepcopy(outcomes)

    adjusted = deepcopy(outcomes)

    for outcome in adjusted:
        base_weight = outcome.get("weight", 0)
        outcome_type = outcome.get("type")

        if not isinstance(base_weight, int):
            continue

        if outcome_type in {"reward", "mixed", "hidden"}:
            outcome["weight"] = max(1, base_weight + 5)
        elif outcome_type in {"empty", "penalty", "ambush"}:
            outcome["weight"] = max(1, base_weight - 4)
        else:
            outcome["weight"] = max(1, base_weight)

    return adjusted


def apply_session_modifiers_to_outcomes(
    outcomes: list[dict[str, Any]],
    *,
    session_modifiers: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Заготовка под сессионные модификаторы.
    Пока поддерживаем простой режим:
    session_modifiers = {
        "reward_bonus": 0,
        "risk_bonus": 0
    }
    """
    session_modifiers = session_modifiers or {}
    adjusted = deepcopy(outcomes)

    reward_bonus = session_modifiers.get("reward_bonus", 0)
    risk_bonus = session_modifiers.get("risk_bonus", 0)

    if not isinstance(reward_bonus, int):
        reward_bonus = 0
    if not isinstance(risk_bonus, int):
        risk_bonus = 0

    for outcome in adjusted:
        base_weight = outcome.get("weight", 0)
        outcome_type = outcome.get("type")

        if not isinstance(base_weight, int):
            continue

        if outcome_type in {"reward", "mixed", "hidden"}:
            outcome["weight"] = max(1, base_weight + reward_bonus)
        elif outcome_type in {"penalty", "ambush"}:
            outcome["weight"] = max(1, base_weight + risk_bonus)
        else:
            outcome["weight"] = max(1, base_weight)

    return adjusted

def build_outcome_weights_snapshot(
    outcomes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    snapshot = []

    for outcome in outcomes or []:
        if not isinstance(outcome, dict):
            continue

        snapshot.append(
            {
                "type": outcome.get("type"),
                "text": outcome.get("text"),
                "weight": outcome.get("weight"),
            }
        )

    return snapshot

def roll_weighted_outcome(
    outcomes: list[dict[str, Any]],
    *,
    rng: random.Random | None = None,
) -> dict[str, Any]:
    if not outcomes:
        raise ValueError("Список outcomes пуст")

    rng = rng or random.Random()

    weighted_pool: list[tuple[int, dict[str, Any]]] = []
    total_weight = 0

    for outcome in outcomes:
        weight = outcome.get("weight", 0)
        if not isinstance(weight, int) or weight <= 0:
            continue

        total_weight += weight
        weighted_pool.append((total_weight, outcome))

    if total_weight <= 0 or not weighted_pool:
        raise ValueError("Нет валидных outcome с положительным весом")

    roll = rng.randint(1, total_weight)

    for threshold, outcome in weighted_pool:
        if roll <= threshold:
            return deepcopy(outcome)

    return deepcopy(weighted_pool[-1][1])


def build_effect_data_from_outcome(outcome: dict[str, Any]) -> dict[str, int]:
    """
    Переводит outcome в effect_data для apply_house_effect().
    Поддерживаем только числовые эффекты для ресурсов.
    Нечисловые reward/penalty-теги не теряем — они уйдут в meta.
    """
    effect_data: dict[str, int] = {}

    reward = outcome.get("reward", {})
    penalty = outcome.get("penalty", {})

    if isinstance(reward, dict):
        for key, value in reward.items():
            if isinstance(value, int):
                effect_data[key] = effect_data.get(key, 0) + value

    if isinstance(penalty, dict):
        for key, value in penalty.items():
            if isinstance(value, int):
                effect_data[key] = effect_data.get(key, 0) + value

    return effect_data


def extract_non_numeric_meta(outcome: dict[str, Any]) -> dict[str, Any]:
    """
    Отдельно вытаскиваем нефинансовые/нетиповые эффекты:
    access_tag, hidden_signal, deal_advantage, foreign_contact и т.д.
    """
    meta: dict[str, Any] = {
        "reward_meta": {},
        "penalty_meta": {},
    }

    reward = outcome.get("reward", {})
    penalty = outcome.get("penalty", {})

    if isinstance(reward, dict):
        for key, value in reward.items():
            if not isinstance(value, int):
                meta["reward_meta"][key] = value

    if isinstance(penalty, dict):
        for key, value in penalty.items():
            if not isinstance(value, int):
                meta["penalty_meta"][key] = value

    return meta


def calculate_location_outcome(
    catalog: dict[str, dict[str, Any]],
    *,
    location_code: str,
    roles: list[str] | None = None,
    visit_count: int = 0,
    session_modifiers: dict[str, Any] | None = None,
    house_tags: list[str] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Главный расчёт:
    - ищем локацию
    - проверяем доступ
    - применяем repeat penalty
    - применяем role modifiers
    - применяем session modifiers
    - роллим outcome
    - считаем риск экспедиции
    - при высоком риске роллим осложнение
    - жёсткий срыв выгоды применяем только к экспедиции
    """
    location = get_location_by_code(catalog, location_code)

    allowed, reason = location_is_available_for_house(
        location,
        house_tags=house_tags,
    )
    if not allowed:
        return {
            "ok": False,
            "message": "Локация недоступна",
            "location_code": location_code,
            "reason": reason,
        }

    outcomes = location.get("outcomes", [])
    if not isinstance(outcomes, list) or not outcomes:
        return {
            "ok": False,
            "message": "У локации нет outcome",
            "location_code": location_code,
        }

    roles = roles or []
    session_modifiers = session_modifiers or {}

    repeat_penalty = location.get("repeat_penalty", 0)
    if not isinstance(repeat_penalty, int):
        repeat_penalty = 0

    is_expedition = bool(session_modifiers.get("is_expedition"))

    base_weights = build_outcome_weights_snapshot(outcomes)

    after_repeat_penalty = apply_repeat_penalty_to_outcomes(
        outcomes,
        visit_count=visit_count,
        repeat_penalty=repeat_penalty,
    )
    after_repeat_penalty_weights = build_outcome_weights_snapshot(after_repeat_penalty)

    after_role_modifiers = apply_role_modifiers_to_outcomes(
        location,
        after_repeat_penalty,
        roles=roles,
    )
    after_role_modifiers_weights = build_outcome_weights_snapshot(after_role_modifiers)

    after_session_modifiers = apply_session_modifiers_to_outcomes(
        after_role_modifiers,
        session_modifiers=session_modifiers,
    )
    final_weights = build_outcome_weights_snapshot(after_session_modifiers)

    rng = random.Random(seed)
    rolled_outcome = roll_weighted_outcome(after_session_modifiers, rng=rng)

    original_outcome_effect_data = build_effect_data_from_outcome(rolled_outcome)
    meta = extract_non_numeric_meta(rolled_outcome)

    base_risk = location.get("risk_level", 0)
    if not isinstance(base_risk, int):
        base_risk = 0

    risk_reduction = session_modifiers.get("risk_reduction", 0)
    if not isinstance(risk_reduction, int):
        risk_reduction = 0

    command_bonus = session_modifiers.get("command_bonus", 0)
    if not isinstance(command_bonus, int):
        command_bonus = 0

    hidden_bonus = session_modifiers.get("hidden_bonus", 0)
    if not isinstance(hidden_bonus, int):
        hidden_bonus = 0

    penalty_reduction = session_modifiers.get("penalty_reduction", 0)
    if not isinstance(penalty_reduction, int):
        penalty_reduction = 0

    visit_risk_pressure = max(0, visit_count - 1) * 4
    hidden_risk_shift = min(hidden_bonus * 2, 6)
    command_risk_shift = min(command_bonus * 2, 4)
    penalty_softening = min(penalty_reduction * 2, 6)

    final_risk_score = base_risk
    final_risk_score += visit_risk_pressure
    final_risk_score -= risk_reduction * 8
    final_risk_score -= hidden_risk_shift
    final_risk_score -= command_risk_shift
    final_risk_score -= penalty_softening

    if final_risk_score < 0:
        final_risk_score = 0
    if final_risk_score > 100:
        final_risk_score = 100

    if final_risk_score <= 15:
        risk_tier = "low"
    elif final_risk_score <= 35:
        risk_tier = "guarded"
    elif final_risk_score <= 60:
        risk_tier = "dangerous"
    else:
        risk_tier = "critical"

    # -------------------------
    # Роллим осложнение от риска
    # -------------------------
    if risk_tier == "low":
        complication_chance = 0
    elif risk_tier == "guarded":
        complication_chance = 15
    elif risk_tier == "dangerous":
        complication_chance = 40
    else:
        complication_chance = 70

    complication_roll = rng.randint(1, 100)
    complication_triggered = complication_roll <= complication_chance

    risk_event = None
    risk_effect_data = {}

    if complication_triggered:
        complication_pool = [
            {
                "code": "fatigue",
                "text": "Экспедиция вымоталась и потеряла темп.",
                "effect_data": {"influence": -1},
            },
            {
                "code": "loss_of_supplies",
                "text": "Часть добычи и запасов ушла в потери.",
                "effect_data": {"wood": -1},
            },
            {
                "code": "alarm",
                "text": "Шум привлёк лишнее внимание.",
                "effect_data": {"influence": -1, "scroll": -1},
            },
        ]

        if risk_tier == "critical":
            complication_pool.append(
                {
                    "code": "hard_setback",
                    "text": "Экспедиция попала в серьёзное осложнение.",
                    "effect_data": {"influence": -2, "wood": -1},
                }
            )

        risk_event = rng.choice(complication_pool)
        risk_effect_data = dict(risk_event.get("effect_data", {}))

        if penalty_reduction > 0:
            softened = {}
            for key, value in risk_effect_data.items():
                if isinstance(value, int) and value < 0:
                    softened_value = value + penalty_reduction
                    if softened_value > 0:
                        softened_value = 0
                    softened[key] = softened_value
                else:
                    softened[key] = value
            risk_effect_data = softened

            risk_event = {
                "code": risk_event.get("code"),
                "text": risk_event.get("text"),
                "effect_data": risk_effect_data,
            }

    # -------------------------
    # Срыв части выгоды только для экспедиции
    # -------------------------
    outcome_effect_data = dict(original_outcome_effect_data)
    expedition_failure_debug = {
        "failure_applied": False,
        "failure_severity": None,
        "reward_cut": {},
        "extra_penalty": {},
        "is_expedition": is_expedition,
    }

    if is_expedition and complication_triggered and risk_tier in {"dangerous", "critical"}:
        cut_ratio = 1 if risk_tier == "dangerous" else 2

        reward_cut = {}
        for key, value in outcome_effect_data.items():
            if isinstance(value, int) and value > 0:
                reduced_value = value - cut_ratio
                if reduced_value < 0:
                    reduced_value = 0
                reward_cut[key] = value - reduced_value
                outcome_effect_data[key] = reduced_value

        extra_penalty = {}

        if not any(isinstance(v, int) and v > 0 for v in outcome_effect_data.values()):
            if risk_tier == "dangerous":
                extra_penalty = {"influence": -1}
            else:
                extra_penalty = {"influence": -1, "wood": -1}

        for key, value in extra_penalty.items():
            outcome_effect_data[key] = outcome_effect_data.get(key, 0) + value

        expedition_failure_debug = {
            "failure_applied": True,
            "failure_severity": risk_tier,
            "reward_cut": reward_cut,
            "extra_penalty": extra_penalty,
            "is_expedition": is_expedition,
        }

        if risk_event is None:
            risk_event = {
                "code": "risk_breakthrough_failed",
                "text": "Высокий риск сорвал часть выгоды экспедиции.",
                "effect_data": extra_penalty,
            }
        else:
            risk_event = {
                "code": risk_event.get("code"),
                "text": risk_event.get("text"),
                "effect_data": risk_effect_data,
                "failure_note": "Высокий риск сорвал часть выгоды экспедиции.",
            }

    combined_effect_data = dict(outcome_effect_data)

    for key, value in risk_effect_data.items():
        if not isinstance(value, int):
            continue
        combined_effect_data[key] = combined_effect_data.get(key, 0) + value

    outcome_debug = {
        "visit_count_before": visit_count,
        "repeat_penalty": repeat_penalty,
        "roles": roles,
        "session_modifiers": session_modifiers,
        "preferred_roles": location.get("preferred_roles", []),
        "base_weights": base_weights,
        "after_repeat_penalty": after_repeat_penalty_weights,
        "after_role_modifiers": after_role_modifiers_weights,
        "final_weights": final_weights,
        "rolled_outcome_type": rolled_outcome.get("type"),
        "rolled_outcome_text": rolled_outcome.get("text"),
    }

    expedition_risk_debug = {
        "base_risk": base_risk,
        "visit_risk_pressure": visit_risk_pressure,
        "risk_reduction": risk_reduction,
        "hidden_risk_shift": hidden_risk_shift,
        "command_risk_shift": command_risk_shift,
        "penalty_softening": penalty_softening,
        "final_risk_score": final_risk_score,
        "risk_tier": risk_tier,
    }

    risk_event_debug = {
        "complication_chance": complication_chance,
        "complication_roll": complication_roll,
        "complication_triggered": complication_triggered,
        "risk_event_code": risk_event.get("code") if risk_event else None,
        "is_expedition": is_expedition,
    }

    return {
        "ok": True,
        "location": {
            "code": location.get("code"),
            "name": location.get("name"),
            "type": location.get("type"),
            "difficulty": location.get("difficulty"),
            "risk_level": location.get("risk_level"),
            "summary": location.get("summary"),
            "preferred_roles": location.get("preferred_roles", []),
            "requires_any_tag": location.get("requires_any_tag", []),
        },
        "visit_count_before": visit_count,
        "rolled_outcome": rolled_outcome,
        "effect_data": combined_effect_data,
        "outcome_effect_data": outcome_effect_data,
        "risk_effect_data": risk_effect_data,
        "risk_event": risk_event,
        "meta": meta,
        "outcome_debug": outcome_debug,
        "expedition_risk_debug": expedition_risk_debug,
        "risk_event_debug": risk_event_debug,
        "expedition_failure_debug": expedition_failure_debug,
    }
def apply_location_outcome_to_house(
    db: Session,
    *,
    house: House,
    calculated_outcome: dict[str, Any],
) -> dict[str, Any]:
    """
    Применяет outcome к дому через уже существующий resource_service.
    Золото пойдёт через gold_service внутри apply_house_effect().
    """
    if not calculated_outcome.get("ok"):
        return {
            "ok": False,
            "message": "Нельзя применить outcome, расчёт завершился ошибкой",
            "outcome": calculated_outcome,
        }

    effect_data = calculated_outcome.get("effect_data", {})
    if not isinstance(effect_data, dict):
        effect_data = {}

    effect_result = apply_house_effect(
        db=db,
        house=house,
        effect_data=effect_data,
    )

    return {
        "ok": True,
        "location": calculated_outcome.get("location"),
        "rolled_outcome": calculated_outcome.get("rolled_outcome"),
        "effect_data": effect_data,
        "meta": calculated_outcome.get("meta", {}),
        "effect_result": effect_result,
    }


def explore_location_for_house(
    db: Session,
    *,
    catalog: dict[str, dict[str, Any]],
    house: House,
    location_code: str,
    roles: list[str] | None = None,
    visit_count: int = 0,
    house_tags: list[str] | None = None,
    session_modifiers: dict[str, Any] | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Удобная склейка:
    calculate -> apply
    """
    calculated = calculate_location_outcome(
        catalog,
        location_code=location_code,
        roles=roles or [],
        visit_count=visit_count,
        house_tags=house_tags or [],
        session_modifiers=session_modifiers or {},
        seed=seed,
    )

    if not calculated.get("ok"):
        return calculated

    applied = apply_location_outcome_to_house(
        db=db,
        house=house,
        calculated_outcome=calculated,
    )

    return {
        "ok": applied.get("ok", False),
        "location": calculated.get("location"),
        "rolled_outcome": calculated.get("rolled_outcome"),
        "effect_data": calculated.get("effect_data"),
        "outcome_effect_data": calculated.get("outcome_effect_data"),
        "risk_effect_data": calculated.get("risk_effect_data"),
        "risk_event": calculated.get("risk_event"),
        "meta": calculated.get("meta"),
        "effect_result": applied.get("effect_result"),
        "visit_count_before": calculated.get("visit_count_before"),
        "outcome_debug": calculated.get("outcome_debug", {}),
        "expedition_risk_debug": calculated.get("expedition_risk_debug", {}),
        "risk_event_debug": calculated.get("risk_event_debug", {}),
        "expedition_failure_debug": calculated.get("expedition_failure_debug", {}),
    }