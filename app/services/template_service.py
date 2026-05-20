from pathlib import Path

from sqlalchemy.orm import Session

from app.models.game_template import GameTemplate
from app.models.game_template_house import GameTemplateHouse
from app.models.game_template_role import GameTemplateRole
from app.models.game_template_act import GameTemplateAct
from app.models.game_template_map_node import GameTemplateMapNode
from app.models.game_template_task_pool import GameTemplateTaskPool
from app.models.game_template_task import GameTemplateTask
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate


REQUIRED_TEMPLATE_FILES = [
    "game_template.yaml",
    "houses.yaml",
    "roles.yaml",
    "acts.yaml",
    "map_nodes.yaml",
    "task_pools_diplomat.yaml",
    "task_pools_lord.yaml",
    "task_pools_maester.yaml",
    "task_pools_treasurer.yaml",
    "task_pools_whisper.yaml",
    "events.yaml",
    "rounds.yaml",
    "round_questions.yaml",
]

TASK_POOL_FILES = [
    "task_pools_diplomat.yaml",
    "task_pools_lord.yaml",
    "task_pools_maester.yaml",
    "task_pools_treasurer.yaml",
    "task_pools_whisper.yaml",
]

ROLE_ALLOWED_ASSIGNMENT_TYPES = {
    "lord_lady": {"strategic_choice", "right_of_move", "sanction", "alliance_decision"},
    "diplomat": {"map_route", "negotiation", "embassy_offer", "trade_contact"},
    "maester": {"quiz", "timeline", "matrix", "dossier_sort", "fill_table"},
    "whisper_master": {"truth_lie", "rumor", "hidden_signal", "blackmail"},
    "treasurer": {"treasury_choice", "exchange", "investment", "risk_trade"},
    "house_sworn": {"support_task", "heraldic_step", "field_action"},
}

REQUIRED_ROLE_CODES = {
    "lord_lady",
    "diplomat",
    "maester",
    "treasurer",
    "whisper_master",
    "house_sworn",
}


def load_template_bundle(
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
):
    clean_template_code = template_code.strip()
    template_dir = game_templates_dir / clean_template_code

    if not template_dir.exists() or not template_dir.is_dir():
        return {
            "ok": False,
            "message": "Папка шаблона не найдена",
            "template_code": clean_template_code,
            "expected_path": str(template_dir),
        }

    missing_files = []
    loaded_files = {}
    parse_errors = []

    for file_name in REQUIRED_TEMPLATE_FILES:
        file_path = template_dir / file_name

        if not file_path.exists():
            missing_files.append(file_name)
            continue

        try:
            loaded_files[file_name] = load_yaml_file_fn(file_path)
        except Exception as e:
            parse_errors.append(
                {
                    "file": file_name,
                    "error": str(e),
                }
            )

    if missing_files or parse_errors:
        return {
            "ok": False,
            "message": "Шаблон не прошёл базовую проверку",
            "template_code": clean_template_code,
            "template_dir": str(template_dir),
            "missing_files": missing_files,
            "parse_errors": parse_errors,
            "loaded_files": loaded_files,
        }

    return {
        "ok": True,
        "template_code": clean_template_code,
        "template_dir": str(template_dir),
        "loaded_files": loaded_files,
    }


def run_deep_validation_from_loaded(
    *,
    template_code: str,
    template_dir: str,
    loaded_files: dict,
):
    errors = []
    warnings = []

    game_template = loaded_files.get("game_template.yaml", {})
    houses_data = loaded_files.get("houses.yaml", {})
    roles_data = loaded_files.get("roles.yaml", {})
    acts_data = loaded_files.get("acts.yaml", {})
    map_nodes_data = loaded_files.get("map_nodes.yaml", {})
    events_data = loaded_files.get("events.yaml", {})
    rounds_data = loaded_files.get("rounds.yaml", {})
    round_questions_data = loaded_files.get("round_questions.yaml", {})

    pool_files = {
        "task_pools_diplomat.yaml": loaded_files.get("task_pools_diplomat.yaml", {}),
        "task_pools_lord.yaml": loaded_files.get("task_pools_lord.yaml", {}),
        "task_pools_maester.yaml": loaded_files.get("task_pools_maester.yaml", {}),
        "task_pools_treasurer.yaml": loaded_files.get("task_pools_treasurer.yaml", {}),
        "task_pools_whisper.yaml": loaded_files.get("task_pools_whisper.yaml", {}),
    }

    required_game_template_fields = [
        "template_code",
        "name",
        "version",
        "modules",
        "session_rules",
        "content_strategy",
    ]
    for field_name in required_game_template_fields:
        if field_name not in game_template:
            errors.append(f'game_template.yaml: отсутствует поле "{field_name}"')

    modules = game_template.get("modules", {})
    if not isinstance(modules, dict):
        errors.append('game_template.yaml: поле "modules" должно быть объектом')

    session_rules = game_template.get("session_rules", {})
    if not isinstance(session_rules, dict):
        errors.append('game_template.yaml: поле "session_rules" должно быть объектом')
        session_rules = {}

    content_strategy = game_template.get("content_strategy", {})
    if not isinstance(content_strategy, dict):
        errors.append('game_template.yaml: поле "content_strategy" должно быть объектом')
        content_strategy = {}

    required_session_rule_fields = [
        "acts_total",
        "supported_houses_min",
        "supported_houses_max",
        "recommended_houses",
        "simultaneous_houses_supported",
        "allow_role_overlap_in_small_team",
        "unique_house_roles",
        "mass_roles",
    ]
    for field_name in required_session_rule_fields:
        if field_name not in session_rules:
            errors.append(f'session_rules: отсутствует поле "{field_name}"')

    supported_houses_min = session_rules.get("supported_houses_min")
    supported_houses_max = session_rules.get("supported_houses_max")
    recommended_houses = session_rules.get("recommended_houses")
    simultaneous_houses_supported = session_rules.get("simultaneous_houses_supported")
    acts_total = session_rules.get("acts_total")
    unique_house_roles = session_rules.get("unique_house_roles", [])
    mass_roles = session_rules.get("mass_roles", [])

    if acts_total is not None and (not isinstance(acts_total, int) or acts_total <= 0):
        errors.append("session_rules: acts_total должен быть положительным целым числом")

    if supported_houses_min is not None and (not isinstance(supported_houses_min, int) or supported_houses_min <= 0):
        errors.append("session_rules: supported_houses_min должен быть положительным целым числом")

    if supported_houses_max is not None and (not isinstance(supported_houses_max, int) or supported_houses_max <= 0):
        errors.append("session_rules: supported_houses_max должен быть положительным целым числом")

    if recommended_houses is not None and (not isinstance(recommended_houses, int) or recommended_houses <= 0):
        errors.append("session_rules: recommended_houses должен быть положительным целым числом")

    if simultaneous_houses_supported is not None and (
        not isinstance(simultaneous_houses_supported, int) or simultaneous_houses_supported <= 0
    ):
        errors.append("session_rules: simultaneous_houses_supported должен быть положительным целым числом")

    if (
        isinstance(supported_houses_min, int)
        and isinstance(supported_houses_max, int)
        and supported_houses_min > supported_houses_max
    ):
        errors.append("session_rules: supported_houses_min не может быть больше supported_houses_max")

    if (
        isinstance(recommended_houses, int)
        and isinstance(supported_houses_min, int)
        and recommended_houses < supported_houses_min
    ):
        errors.append("session_rules: recommended_houses не может быть меньше supported_houses_min")

    if (
        isinstance(recommended_houses, int)
        and isinstance(supported_houses_max, int)
        and recommended_houses > supported_houses_max
    ):
        errors.append("session_rules: recommended_houses не может быть больше supported_houses_max")

    if isinstance(simultaneous_houses_supported, int) and simultaneous_houses_supported < 10:
        warnings.append("session_rules: simultaneous_houses_supported меньше 10, а целевой запас заявлен как минимум 10")

    if not isinstance(unique_house_roles, list):
        errors.append('session_rules: поле "unique_house_roles" должно быть списком')

    if not isinstance(mass_roles, list):
        errors.append('session_rules: поле "mass_roles" должно быть списком')

    if content_strategy.get("per_house_variation_required") is not True:
        warnings.append("game_template.yaml: per_house_variation_required лучше держать true")

    if content_strategy.get("avoid_same_assignments_between_houses") is not True:
        warnings.append("game_template.yaml: avoid_same_assignments_between_houses лучше держать true")

    houses = houses_data.get("houses")
    if not isinstance(houses, list):
        errors.append('houses.yaml: ключ "houses" должен быть списком')
        houses = []

    roles = roles_data.get("roles")
    if not isinstance(roles, list):
        errors.append('roles.yaml: ключ "roles" должен быть списком')
        roles = []

    acts = acts_data.get("acts")
    if not isinstance(acts, list):
        errors.append('acts.yaml: ключ "acts" должен быть списком')
        acts = []

    map_nodes = map_nodes_data.get("map_nodes")
    if not isinstance(map_nodes, list):
        errors.append('map_nodes.yaml: ключ "map_nodes" должен быть списком')
        map_nodes = []

    events = events_data.get("events")
    if not isinstance(events, list):
        errors.append('events.yaml: ключ "events" должен быть списком')
        events = []

    rounds = rounds_data.get("rounds")
    if not isinstance(rounds, list):
        errors.append('rounds.yaml: ключ "rounds" должен быть списком')
        rounds = []

    round_questions = round_questions_data.get("round_questions")
    if not isinstance(round_questions, list):
        errors.append('round_questions.yaml: ключ "round_questions" должен быть списком')
        round_questions = []

    if isinstance(supported_houses_min, int) and len(houses) < supported_houses_min:
        errors.append(
            f"houses.yaml: домов меньше supported_houses_min ({supported_houses_min}), сейчас {len(houses)}"
        )

    if isinstance(recommended_houses, int) and len(houses) < recommended_houses:
        warnings.append(
            f"houses.yaml: домов меньше recommended_houses ({recommended_houses}), сейчас {len(houses)}"
        )

    role_codes = set()
    for role_item in roles:
        if not isinstance(role_item, dict):
            errors.append("roles.yaml: каждая роль должна быть объектом")
            continue

        role_code = role_item.get("code")
        role_name = role_item.get("name")
        assignment_types = role_item.get("assignment_types")

        if not role_code:
            errors.append("roles.yaml: у одной из ролей отсутствует code")
            continue

        if role_code in role_codes:
            errors.append(f'roles.yaml: дублируется role code "{role_code}"')
        role_codes.add(role_code)

        if not role_name:
            errors.append(f'roles.yaml: у роли "{role_code}" отсутствует name')

        if not isinstance(assignment_types, list):
            errors.append(f'roles.yaml: у роли "{role_code}" assignment_types должен быть списком')

    missing_required_roles = REQUIRED_ROLE_CODES - role_codes
    if missing_required_roles:
        errors.append(
            "roles.yaml: отсутствуют обязательные роли: " + ", ".join(sorted(missing_required_roles))
        )

    house_keys = set()
    for house_item in houses:
        if not isinstance(house_item, dict):
            errors.append("houses.yaml: каждый дом должен быть объектом")
            continue

        house_key = house_item.get("house_key")
        name = house_item.get("name")

        if not house_key:
            errors.append("houses.yaml: у одного из домов отсутствует house_key")
            continue

        if house_key in house_keys:
            errors.append(f'houses.yaml: дублируется house_key "{house_key}"')
        house_keys.add(house_key)

        if not name:
            errors.append(f'houses.yaml: у дома "{house_key}" отсутствует name')

    act_numbers = set()
    for act_item in acts:
        if not isinstance(act_item, dict):
            errors.append("acts.yaml: каждый акт должен быть объектом")
            continue

        act_number = act_item.get("act_number")
        if act_number is None:
            errors.append("acts.yaml: у одного из актов отсутствует act_number")
            continue

        if act_number in act_numbers:
            errors.append(f'acts.yaml: дублируется act_number "{act_number}"')
        act_numbers.add(act_number)

    discovered_pool_codes = set()
    pools_by_role = {}

    for pool_file_name, pool_file_data in pool_files.items():
        pools = pool_file_data.get("pools")
        if not isinstance(pools, list):
            errors.append(f'{pool_file_name}: ключ "pools" должен быть списком')
            continue

        for pool_item in pools:
            if not isinstance(pool_item, dict):
                errors.append(f"{pool_file_name}: каждый pool должен быть объектом")
                continue

            pool_code = pool_item.get("pool_code")
            role_code = pool_item.get("role_code")
            assignment_type = pool_item.get("assignment_type")
            tasks = pool_item.get("tasks")

            if not pool_code:
                errors.append(f"{pool_file_name}: у одного из pool отсутствует pool_code")
            else:
                if pool_code in discovered_pool_codes:
                    errors.append(f'{pool_file_name}: дублируется pool_code "{pool_code}"')
                discovered_pool_codes.add(pool_code)

            if not role_code:
                errors.append(f"{pool_file_name}: у pool отсутствует role_code")
            elif role_code not in role_codes:
                errors.append(f'{pool_file_name}: role_code "{role_code}" не найден в roles.yaml')

            if not assignment_type:
                errors.append(f"{pool_file_name}: у pool отсутствует assignment_type")
            elif role_code in ROLE_ALLOWED_ASSIGNMENT_TYPES:
                if assignment_type not in ROLE_ALLOWED_ASSIGNMENT_TYPES[role_code]:
                    errors.append(
                        f'{pool_file_name}: assignment_type "{assignment_type}" не подходит роли "{role_code}"'
                    )

            if not isinstance(tasks, list) or len(tasks) == 0:
                warnings.append(f'{pool_file_name}: pool "{pool_code}" не содержит задач')

            if role_code:
                pools_by_role.setdefault(role_code, 0)
                pools_by_role[role_code] += 1

    for required_role in ["lord_lady", "diplomat", "maester", "treasurer", "whisper_master"]:
        if pools_by_role.get(required_role, 0) == 0:
            errors.append(f'Нет ни одного pool для роли "{required_role}"')

    for node_item in map_nodes:
        if not isinstance(node_item, dict):
            errors.append("map_nodes.yaml: каждая точка карты должна быть объектом")
            continue

        node_code = node_item.get("node_code")
        visible_for_roles = node_item.get("visible_for_roles", [])
        payload = node_item.get("payload", {})
        result_mode = node_item.get("result_mode")

        if not node_code:
            errors.append("map_nodes.yaml: у одной из точек отсутствует node_code")

        if not isinstance(visible_for_roles, list):
            errors.append(f'map_nodes.yaml: у точки "{node_code}" visible_for_roles должен быть списком')
        else:
            for role_code in visible_for_roles:
                if role_code != "*" and role_code not in role_codes:
                    errors.append(
                        f'map_nodes.yaml: у точки "{node_code}" используется неизвестная роль "{role_code}"'
                    )

        if result_mode == "assignment_from_pool":
            pool_code = payload.get("pool_code") if isinstance(payload, dict) else None
            if not pool_code:
                errors.append(
                    f'map_nodes.yaml: у точки "{node_code}" result_mode=assignment_from_pool, но нет payload.pool_code'
                )
            elif pool_code not in discovered_pool_codes:
                errors.append(
                    f'map_nodes.yaml: у точки "{node_code}" используется неизвестный pool_code "{pool_code}"'
                )

    round_codes = set()

    for round_item in rounds:
        if not isinstance(round_item, dict):
            errors.append("rounds.yaml: каждый round должен быть объектом")
            continue

        round_code = round_item.get("round_code")
        title = round_item.get("title")
        act_number = round_item.get("act_number")
        round_kind = round_item.get("round_kind")
        check_mode = round_item.get("check_mode")
        questions_total = round_item.get("questions_total")
        question_transition_mode = round_item.get("question_transition_mode")
        round_transition_mode = round_item.get("round_transition_mode")

        if not round_code:
            errors.append("rounds.yaml: у одного из раундов отсутствует round_code")
            continue

        if round_code in round_codes:
            errors.append(f'rounds.yaml: дублируется round_code "{round_code}"')
        round_codes.add(round_code)

        if not title:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует title')

        if act_number is None:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует act_number')

        if not round_kind:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует round_kind')

        if not check_mode:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует check_mode')

        if questions_total is None:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует questions_total')

        if not question_transition_mode:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует question_transition_mode')
        elif question_transition_mode not in {"auto", "manual"}:
            errors.append(
                f'rounds.yaml: у раунда "{round_code}" question_transition_mode должен быть "auto" или "manual"'
            )

        if not round_transition_mode:
            errors.append(f'rounds.yaml: у раунда "{round_code}" отсутствует round_transition_mode')
        elif round_transition_mode not in {"auto", "manual"}:
            errors.append(
                f'rounds.yaml: у раунда "{round_code}" round_transition_mode должен быть "auto" или "manual"'
            )

    question_codes = set()
    questions_count_by_round = {}

    for question_item in round_questions:
        if not isinstance(question_item, dict):
            errors.append("round_questions.yaml: каждый вопрос должен быть объектом")
            continue

        round_code = question_item.get("round_code")
        question_code = question_item.get("question_code")
        sequence_no = question_item.get("sequence_no")
        prompt = question_item.get("prompt")
        ui_template = question_item.get("ui_template")
        answer_mode = question_item.get("answer_mode")

        if not round_code:
            errors.append("round_questions.yaml: у одного из вопросов отсутствует round_code")
            continue

        if round_code not in round_codes:
            errors.append(
                f'round_questions.yaml: вопрос "{question_code}" ссылается на неизвестный round_code "{round_code}"'
            )

        if not question_code:
            errors.append(f'round_questions.yaml: у вопроса раунда "{round_code}" отсутствует question_code')
            continue

        if question_code in question_codes:
            errors.append(f'round_questions.yaml: дублируется question_code "{question_code}"')
        question_codes.add(question_code)

        if sequence_no is None:
            errors.append(f'round_questions.yaml: у вопроса "{question_code}" отсутствует sequence_no')

        if not prompt:
            errors.append(f'round_questions.yaml: у вопроса "{question_code}" отсутствует prompt')

        if not ui_template:
            errors.append(f'round_questions.yaml: у вопроса "{question_code}" отсутствует ui_template')

        if not answer_mode:
            errors.append(f'round_questions.yaml: у вопроса "{question_code}" отсутствует answer_mode')

        questions_count_by_round.setdefault(round_code, 0)
        questions_count_by_round[round_code] += 1

    for round_item in rounds:
        round_code = round_item.get("round_code")
        expected_questions_total = round_item.get("questions_total")

        if round_code and isinstance(expected_questions_total, int):
            actual_questions_total = questions_count_by_round.get(round_code, 0)
            if actual_questions_total != expected_questions_total:
                warnings.append(
                    f'Раунд "{round_code}": questions_total={expected_questions_total}, но в round_questions.yaml найдено вопросов: {actual_questions_total}'
                )

    summary = {
        "template_code": template_code,
        "template_dir": template_dir,
        "houses_count": len(houses),
        "roles_count": len(roles),
        "acts_count": len(acts),
        "map_nodes_count": len(map_nodes),
        "events_count": len(events),
        "rounds_count": len(rounds),
        "round_questions_count": len(round_questions),
        "pool_codes_count": len(discovered_pool_codes),
        "pools_by_role": pools_by_role,
    }

    return {
        "ok": len(errors) == 0,
        "message": "Глубокая валидация завершена",
        "summary": summary,
        "errors": errors,
        "warnings": warnings,
        "loaded_data": {
            "game_template": game_template,
            "houses": houses,
            "roles": roles,
            "acts": acts,
            "map_nodes": map_nodes,
            "rounds": rounds,
            "round_questions": round_questions,
            "task_pool_files": pool_files,
        },
    }


def validate_template_logic(
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
    safe_list_length_fn,
):
    clean_template_code = template_code.strip()
    template_dir = game_templates_dir / clean_template_code

    if not template_dir.exists() or not template_dir.is_dir():
        return {
            "ok": False,
            "message": "Папка шаблона не найдена",
            "template_code": clean_template_code,
            "expected_path": str(template_dir),
        }

    missing_files = []
    loaded_files = {}
    parse_errors = []

    for file_name in REQUIRED_TEMPLATE_FILES:
        file_path = template_dir / file_name

        if not file_path.exists():
            missing_files.append(file_name)
            continue

        try:
            data = load_yaml_file_fn(file_path)
            loaded_files[file_name] = data
        except Exception as e:
            parse_errors.append(
                {
                    "file": file_name,
                    "error": str(e),
                }
            )

    if missing_files or parse_errors:
        return {
            "ok": False,
            "message": "Шаблон не прошёл базовую проверку",
            "template_code": clean_template_code,
            "template_dir": str(template_dir),
            "missing_files": missing_files,
            "parse_errors": parse_errors,
            "loaded_files_count": len(loaded_files),
        }

    summary = {
        "template_code": clean_template_code,
        "template_dir": str(template_dir),
        "game_template_name": loaded_files.get("game_template.yaml", {}).get("name"),
        "game_template_version": loaded_files.get("game_template.yaml", {}).get("version"),
        "houses_count": safe_list_length_fn(loaded_files.get("houses.yaml", {}), "houses"),
        "roles_count": safe_list_length_fn(loaded_files.get("roles.yaml", {}), "roles"),
        "acts_count": safe_list_length_fn(loaded_files.get("acts.yaml", {}), "acts"),
        "map_nodes_count": safe_list_length_fn(loaded_files.get("map_nodes.yaml", {}), "map_nodes"),
        "events_count": safe_list_length_fn(loaded_files.get("events.yaml", {}), "events"),
        "diplomat_pools_count": safe_list_length_fn(loaded_files.get("task_pools_diplomat.yaml", {}), "pools"),
        "lord_pools_count": safe_list_length_fn(loaded_files.get("task_pools_lord.yaml", {}), "pools"),
        "maester_pools_count": safe_list_length_fn(loaded_files.get("task_pools_maester.yaml", {}), "pools"),
        "treasurer_pools_count": safe_list_length_fn(loaded_files.get("task_pools_treasurer.yaml", {}), "pools"),
        "whisper_pools_count": safe_list_length_fn(loaded_files.get("task_pools_whisper.yaml", {}), "pools"),
    }

    return {
        "ok": True,
        "message": "Шаблон прошёл базовую проверку",
        "summary": summary,
        "files_checked": REQUIRED_TEMPLATE_FILES,
    }


def import_template_core_preview_logic(
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
):
    bundle = load_template_bundle(
        template_code=template_code,
        game_templates_dir=game_templates_dir,
        load_yaml_file_fn=load_yaml_file_fn,
    )

    if not bundle.get("ok"):
        return bundle

    deep_result = run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

    if not deep_result.get("ok"):
        return {
            "ok": False,
            "message": "Dry-run импорт остановлен: шаблон не прошёл глубокую валидацию",
            "validation": {
                "errors": deep_result.get("errors", []),
                "warnings": deep_result.get("warnings", []),
                "summary": deep_result.get("summary", {}),
            },
        }

    loaded_data = deep_result.get("loaded_data", {})
    game_template = loaded_data.get("game_template", {})
    houses = loaded_data.get("houses", [])
    roles = loaded_data.get("roles", [])
    acts = loaded_data.get("acts", [])

    imported_template_preview = {
        "template_code": game_template.get("template_code"),
        "name": game_template.get("name"),
        "version": game_template.get("version"),
        "description": game_template.get("description"),
        "modules": list(game_template.get("modules", {}).keys()),
        "session_rules": game_template.get("session_rules", {}),
    }

    houses_preview = [
        {
            "house_key": house.get("house_key"),
            "name": house.get("name"),
            "theme_tags": house.get("theme_tags", []),
        }
        for house in houses
    ]

    roles_preview = [
        {
            "code": role.get("code"),
            "name": role.get("name"),
            "ui_track": role.get("ui_track"),
            "assignment_types_count": len(role.get("assignment_types", []))
            if isinstance(role.get("assignment_types"), list)
            else 0,
        }
        for role in roles
    ]

    acts_preview = [
        {
            "act_number": act.get("act_number"),
            "name": act.get("name"),
            "enabled_assignment_types_count": len(act.get("enabled_assignment_types", []))
            if isinstance(act.get("enabled_assignment_types"), list)
            else 0,
        }
        for act in acts
    ]

    return {
        "ok": True,
        "message": "Dry-run импорт ядра шаблона прошёл успешно",
        "note": "Это пока только preview. В БД ничего не записано.",
        "import_preview": {
            "template": imported_template_preview,
            "houses_count": len(houses_preview),
            "roles_count": len(roles_preview),
            "acts_count": len(acts_preview),
            "houses": houses_preview,
            "roles": roles_preview,
            "acts": acts_preview,
        },
        "validation_warnings": deep_result.get("warnings", []),
    }


def import_template_core_real_logic(
    db: Session,
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
    dump_json_fn,
):
    bundle = load_template_bundle(
        template_code=template_code,
        game_templates_dir=game_templates_dir,
        load_yaml_file_fn=load_yaml_file_fn,
    )

    if not bundle.get("ok"):
        return bundle

    deep_result = run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

    if not deep_result.get("ok"):
        return {
            "ok": False,
            "message": "Реальный импорт остановлен: шаблон не прошёл глубокую валидацию",
            "validation": {
                "errors": deep_result.get("errors", []),
                "warnings": deep_result.get("warnings", []),
                "summary": deep_result.get("summary", {}),
            },
        }

    loaded_data = deep_result.get("loaded_data", {})
    game_template_data = loaded_data.get("game_template", {})
    houses = loaded_data.get("houses", [])
    roles = loaded_data.get("roles", [])
    acts = loaded_data.get("acts", [])

    session_rules = game_template_data.get("session_rules", {})

    template = (
        db.query(GameTemplate)
        .filter(GameTemplate.template_code == game_template_data.get("template_code"))
        .first()
    )

    created = False
    if not template:
        template = GameTemplate(
            template_code=game_template_data.get("template_code"),
        )
        db.add(template)
        created = True

    template.name = game_template_data.get("name")
    template.version = game_template_data.get("version", 1)
    template.description = game_template_data.get("description")

    template.default_team_size_min = game_template_data.get("default_team_size_min")
    template.default_team_size_max = game_template_data.get("default_team_size_max")

    template.acts_total = session_rules.get("acts_total")
    template.supported_houses_min = session_rules.get("supported_houses_min")
    template.supported_houses_max = session_rules.get("supported_houses_max")
    template.recommended_houses = session_rules.get("recommended_houses")
    template.simultaneous_houses_supported = session_rules.get("simultaneous_houses_supported")
    template.allow_role_overlap_in_small_team = str(
        session_rules.get("allow_role_overlap_in_small_team")
    )

    db.commit()
    db.refresh(template)

    imported_houses = []
    for house in houses:
        existing_house = (
            db.query(GameTemplateHouse)
            .filter(
                GameTemplateHouse.template_id == template.id,
                GameTemplateHouse.house_key == house.get("house_key"),
            )
            .first()
        )

        if not existing_house:
            existing_house = GameTemplateHouse(
                template_id=template.id,
                house_key=house.get("house_key"),
            )
            db.add(existing_house)

        content_bias = house.get("content_bias", {}) if isinstance(house.get("content_bias"), dict) else {}

        existing_house.name = house.get("name")
        existing_house.theme_tags = dump_json_fn(house.get("theme_tags", []))
        existing_house.diplomat_bias = dump_json_fn(content_bias.get("diplomat", []))
        existing_house.maester_bias = dump_json_fn(content_bias.get("maester", []))
        existing_house.whisper_bias = dump_json_fn(content_bias.get("whisper_master", []))
        existing_house.treasurer_bias = dump_json_fn(content_bias.get("treasurer", []))
        existing_house.lord_bias = dump_json_fn(content_bias.get("lord_lady", []))

        imported_houses.append(house.get("house_key"))

    imported_roles = []
    for role in roles:
        existing_role = (
            db.query(GameTemplateRole)
            .filter(
                GameTemplateRole.template_id == template.id,
                GameTemplateRole.code == role.get("code"),
            )
            .first()
        )

        if not existing_role:
            existing_role = GameTemplateRole(
                template_id=template.id,
                code=role.get("code"),
            )
            db.add(existing_role)

        existing_role.name = role.get("name")
        existing_role.ui_track = role.get("ui_track")
        existing_role.assignment_types = dump_json_fn(role.get("assignment_types", []))

        imported_roles.append(role.get("code"))

    imported_acts = []
    for act in acts:
        existing_act = (
            db.query(GameTemplateAct)
            .filter(
                GameTemplateAct.template_id == template.id,
                GameTemplateAct.act_number == act.get("act_number"),
            )
            .first()
        )

        if not existing_act:
            existing_act = GameTemplateAct(
                template_id=template.id,
                act_number=act.get("act_number"),
            )
            db.add(existing_act)

        existing_act.name = act.get("name")
        existing_act.enabled_assignment_types = dump_json_fn(act.get("enabled_assignment_types", []))
        existing_act.event_tags = dump_json_fn(act.get("event_tags", []))

        imported_acts.append(act.get("act_number"))

    db.commit()

    return {
        "ok": True,
        "message": "Реальный импорт ядра шаблона завершён",
        "template_created_now": created,
        "template": {
            "id": template.id,
            "template_code": template.template_code,
            "name": template.name,
            "version": template.version,
        },
        "imported_counts": {
            "houses": len(imported_houses),
            "roles": len(imported_roles),
            "acts": len(imported_acts),
        },
        "imported_keys": {
            "houses": imported_houses,
            "roles": imported_roles,
            "acts": imported_acts,
        },
        "validation_warnings": deep_result.get("warnings", []),
    }


def import_template_map_real_logic(
    db: Session,
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
    dump_json_fn,
):
    bundle = load_template_bundle(
        template_code=template_code,
        game_templates_dir=game_templates_dir,
        load_yaml_file_fn=load_yaml_file_fn,
    )

    if not bundle.get("ok"):
        return bundle

    deep_result = run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

    if not deep_result.get("ok"):
        return {
            "ok": False,
            "message": "Импорт карты остановлен: шаблон не прошёл глубокую валидацию",
            "validation": {
                "errors": deep_result.get("errors", []),
                "warnings": deep_result.get("warnings", []),
                "summary": deep_result.get("summary", {}),
            },
        }

    template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()
    if not template:
        return {
            "ok": False,
            "message": "Сначала импортируйте ядро шаблона",
            "required_route": f"/dev/import-template-core-real/{template_code}",
        }

    loaded_data = deep_result.get("loaded_data", {})
    map_nodes = loaded_data.get("map_nodes", [])

    imported_nodes = []

    for node in map_nodes:
        existing_node = (
            db.query(GameTemplateMapNode)
            .filter(
                GameTemplateMapNode.template_id == template.id,
                GameTemplateMapNode.node_code == node.get("node_code"),
            )
            .first()
        )

        if not existing_node:
            existing_node = GameTemplateMapNode(
                template_id=template.id,
                node_code=node.get("node_code"),
            )
            db.add(existing_node)

        existing_node.name = node.get("name")
        existing_node.node_type = node.get("node_type")
        existing_node.visible_for_roles = dump_json_fn(node.get("visible_for_roles", []))
        existing_node.visible_for_houses = dump_json_fn(node.get("visible_for_houses", []))
        existing_node.act_min = node.get("act_min")
        existing_node.act_max = node.get("act_max")
        existing_node.move_cost = node.get("move_cost")
        existing_node.result_mode = node.get("result_mode")
        existing_node.payload = dump_json_fn(node.get("payload", {}))

        imported_nodes.append(node.get("node_code"))

    db.commit()

    return {
        "ok": True,
        "message": "Импорт карты шаблона завершён",
        "template": {
            "id": template.id,
            "template_code": template.template_code,
            "name": template.name,
        },
        "imported_nodes_count": len(imported_nodes),
        "imported_node_codes": imported_nodes,
        "validation_warnings": deep_result.get("warnings", []),
    }


def import_template_task_pools_real_logic(
    db: Session,
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
    dump_json_fn,
):
    bundle = load_template_bundle(
        template_code=template_code,
        game_templates_dir=game_templates_dir,
        load_yaml_file_fn=load_yaml_file_fn,
    )

    if not bundle.get("ok"):
        return bundle

    deep_result = run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

    if not deep_result.get("ok"):
        return {
            "ok": False,
            "message": "Импорт пулов остановлен: шаблон не прошёл глубокую валидацию",
            "validation": {
                "errors": deep_result.get("errors", []),
                "warnings": deep_result.get("warnings", []),
                "summary": deep_result.get("summary", {}),
            },
        }

    template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()
    if not template:
        return {
            "ok": False,
            "message": "Сначала импортируйте ядро шаблона",
            "required_route": f"/dev/import-template-core-real/{template_code}",
        }

    loaded_data = deep_result.get("loaded_data", {})
    task_pool_files = loaded_data.get("task_pool_files", {})

    imported_pool_codes = []
    imported_task_codes = []

    for file_name in TASK_POOL_FILES:
        file_data = task_pool_files.get(file_name, {})
        pools = file_data.get("pools", [])

        for pool in pools:
            pool_code = pool.get("pool_code")
            role_code = pool.get("role_code")
            assignment_type = pool.get("assignment_type")
            selection_policy = pool.get("selection_policy")

            existing_pool = (
                db.query(GameTemplateTaskPool)
                .filter(
                    GameTemplateTaskPool.template_id == template.id,
                    GameTemplateTaskPool.pool_code == pool_code,
                )
                .first()
            )

            if not existing_pool:
                existing_pool = GameTemplateTaskPool(
                    template_id=template.id,
                    pool_code=pool_code,
                )
                db.add(existing_pool)

            existing_pool.role_code = role_code
            existing_pool.assignment_type = assignment_type
            existing_pool.selection_policy = selection_policy

            db.commit()
            db.refresh(existing_pool)

            imported_pool_codes.append(pool_code)

            tasks = pool.get("tasks", [])
            for task in tasks:
                task_code = task.get("task_code")

                existing_task = (
                    db.query(GameTemplateTask)
                    .filter(
                        GameTemplateTask.template_id == template.id,
                        GameTemplateTask.task_code == task_code,
                    )
                    .first()
                )

                if not existing_task:
                    existing_task = GameTemplateTask(
                        template_id=template.id,
                        pool_id=existing_pool.id,
                        task_code=task_code,
                    )
                    db.add(existing_task)

                existing_task.pool_id = existing_pool.id
                existing_task.role_code = role_code
                existing_task.assignment_type = assignment_type

                existing_task.title = task.get("title")
                existing_task.prompt = task.get("prompt")
                existing_task.ui_template = task.get("ui_template")

                existing_task.difficulty = task.get("difficulty")
                existing_task.act_min = task.get("act_min")
                existing_task.act_max = task.get("act_max")

                existing_task.allowed_house_keys = dump_json_fn(task.get("allowed_house_keys", []))
                existing_task.content_json = dump_json_fn(task.get("content", {}))
                existing_task.reward_json = dump_json_fn(task.get("reward", {}))
                existing_task.fail_effect_json = dump_json_fn(task.get("fail_effect", {}))

                imported_task_codes.append(task_code)

    db.commit()

    return {
        "ok": True,
        "message": "Импорт пулов и задач шаблона завершён",
        "template": {
            "id": template.id,
            "template_code": template.template_code,
            "name": template.name,
        },
        "imported_counts": {
            "pools": len(imported_pool_codes),
            "tasks": len(imported_task_codes),
        },
        "imported_pool_codes": imported_pool_codes,
        "imported_task_codes": imported_task_codes,
        "validation_warnings": deep_result.get("warnings", []),
    }


def import_template_rounds_real_logic(
    db: Session,
    *,
    template_code: str,
    game_templates_dir: Path,
    load_yaml_file_fn,
    dump_json_fn,
):
    bundle = load_template_bundle(
        template_code=template_code,
        game_templates_dir=game_templates_dir,
        load_yaml_file_fn=load_yaml_file_fn,
    )

    if not bundle.get("ok"):
        return bundle

    deep_result = run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

    if not deep_result.get("ok"):
        return {
            "ok": False,
            "message": "Импорт раундов остановлен: шаблон не прошёл глубокую валидацию",
            "validation": {
                "errors": deep_result.get("errors", []),
                "warnings": deep_result.get("warnings", []),
                "summary": deep_result.get("summary", {}),
            },
        }

    template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()
    if not template:
        return {
            "ok": False,
            "message": "Сначала импортируйте ядро шаблона",
            "required_route": f"/dev/import-template-core-real/{template_code}",
        }

    loaded_data = deep_result.get("loaded_data", {})
    rounds = loaded_data.get("rounds", [])
    round_questions = loaded_data.get("round_questions", [])

    imported_round_codes = []
    imported_question_codes = []

    round_by_code = {}

    for round_item in rounds:
        round_code = round_item.get("round_code")

        existing_round = (
            db.query(RoundTemplate)
            .filter(
                RoundTemplate.template_id == template.id,
                RoundTemplate.round_code == round_code,
            )
            .first()
        )

        if not existing_round:
            existing_round = RoundTemplate(
                template_id=template.id,
                round_code=round_code,
            )
            db.add(existing_round)

        existing_round.title = round_item.get("title")
        existing_round.act_number = round_item.get("act_number")
        existing_round.round_kind = round_item.get("round_kind")
        existing_round.check_mode = round_item.get("check_mode", "auto")
        existing_round.questions_total = round_item.get("questions_total", 1)
        existing_round.time_limit_sec = round_item.get("time_limit_sec")
        existing_round.is_host_led = bool(round_item.get("is_host_led", True))
        existing_round.bar_window_opens = bool(round_item.get("bar_window_opens", False))
        existing_round.scoring_mode = round_item.get("scoring_mode")
        existing_round.question_transition_mode = round_item.get("question_transition_mode", "manual")
        existing_round.round_transition_mode = round_item.get("round_transition_mode", "manual")
        existing_round.intro_text = round_item.get("intro_text")
        existing_round.outro_text = round_item.get("outro_text")

        db.flush()

        round_by_code[round_code] = existing_round
        imported_round_codes.append(round_code)

    for question_item in round_questions:
        round_code = question_item.get("round_code")
        question_code = question_item.get("question_code")

        parent_round = round_by_code.get(round_code)
        if not parent_round:
            continue

        existing_question = (
            db.query(RoundQuestionTemplate)
            .filter(
                RoundQuestionTemplate.round_template_id == parent_round.id,
                RoundQuestionTemplate.question_code == question_code,
            )
            .first()
        )

        if not existing_question:
            existing_question = RoundQuestionTemplate(
                round_template_id=parent_round.id,
                question_code=question_code,
            )
            db.add(existing_question)

        existing_question.sequence_no = question_item.get("sequence_no")
        existing_question.role_code = question_item.get("role_code")
        existing_question.title = question_item.get("title")
        existing_question.prompt = question_item.get("prompt")
        existing_question.ui_template = question_item.get("ui_template")
        existing_question.answer_mode = question_item.get("answer_mode")
        existing_question.auto_check = bool(question_item.get("auto_check", True))
        existing_question.manual_check_allowed = bool(question_item.get("manual_check_allowed", False))
        existing_question.allowed_house_keys = dump_json_fn(question_item.get("allowed_house_keys", []))
        existing_question.content_json = dump_json_fn(question_item.get("content", {}))
        existing_question.reward_json = dump_json_fn(question_item.get("reward", {}))
        existing_question.fail_effect_json = dump_json_fn(question_item.get("fail_effect", {}))

        imported_question_codes.append(question_code)

    db.commit()

    return {
        "ok": True,
        "message": "Импорт раундов и вопросов завершён",
        "template": {
            "id": template.id,
            "template_code": template.template_code,
            "name": template.name,
        },
        "imported_counts": {
            "rounds": len(imported_round_codes),
            "questions": len(imported_question_codes),
        },
        "imported_round_codes": imported_round_codes,
        "imported_question_codes": imported_question_codes,
        "validation_warnings": deep_result.get("warnings", []),
    }