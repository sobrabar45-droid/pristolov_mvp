from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from app.models.house import House
from app.models.house_gold_transaction import HouseGoldTransaction


class GoldError(Exception):
    pass


class GoldInsufficientFundsError(GoldError):
    pass


@dataclass
class GoldChangeResult:
    house_id: int
    amount: int
    balance_before: int
    balance_after: int
    transaction_id: int


GOLD_OPERATION_TYPES = {
    "grant_start",
    "grant_check",
    "grant_expedition",
    "grant_event",
    "grant_manual",
    "spend_action",
    "spend_event",
    "spend_pvp_stake",
    "spend_bar_exchange",
    "spend_manual",
    "refund",
    "pvp_win",
    "pvp_fee",
    "transfer_in",
    "transfer_out",
    "admin_adjustment_in",
    "admin_adjustment_out",
}


def change_house_gold(
    db: Session,
    *,
    house: House,
    amount: int,
    operation_type: str,
    source_type: str,
    reason: str,
    source_id: Optional[int] = None,
    comment: Optional[str] = None,
    performed_by_player_id: Optional[int] = None,
    counterparty_house_id: Optional[int] = None,
    allow_negative: bool = False,
) -> GoldChangeResult:
    if amount == 0:
        raise GoldError("Нулевая операция с золотом запрещена")

    if operation_type not in GOLD_OPERATION_TYPES:
        raise GoldError(f'Недопустимый operation_type: "{operation_type}"')

    balance_before = int(house.resource_gold or 0)
    balance_after = balance_before + amount

    if not allow_negative and balance_after < 0:
        raise GoldInsufficientFundsError(
            f'У дома "{house.name}" недостаточно золота: '
            f"было {balance_before}, изменение {amount}"
        )

    house.resource_gold = balance_after

    tx = HouseGoldTransaction(
        game_id=house.game_id,
        house_id=house.id,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        operation_type=operation_type,
        source_type=source_type,
        source_id=source_id,
        reason=reason,
        comment=comment,
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=counterparty_house_id,
    )
    db.add(tx)
    db.flush()

    return GoldChangeResult(
        house_id=house.id,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        transaction_id=tx.id,
    )


def transfer_gold_between_houses(
    db: Session,
    *,
    from_house: House,
    to_house: House,
    amount: int,
    source_type: str,
    reason: str,
    source_id: Optional[int] = None,
    performed_by_player_id: Optional[int] = None,
):
    if amount <= 0:
        raise GoldError("Перевод золота должен быть больше нуля")

    out_result = change_house_gold(
        db,
        house=from_house,
        amount=-amount,
        operation_type="transfer_out",
        source_type=source_type,
        source_id=source_id,
        reason=reason,
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=to_house.id,
    )

    in_result = change_house_gold(
        db,
        house=to_house,
        amount=amount,
        operation_type="transfer_in",
        source_type=source_type,
        source_id=source_id,
        reason=reason,
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=from_house.id,
    )

    return {
        "from_house": out_result,
        "to_house": in_result,
    }


def calculate_gold_from_check(amount_rub: int) -> int:
    if amount_rub <= 0:
        return 0
    # Утверждённая формула: 500 ₽ = 1 золото
    return amount_rub // 500


def grant_start_gold_for_house(
    db: Session,
    *,
    house: House,
    players_count: int,
):
    if players_count <= 0:
        raise GoldError("players_count должен быть больше нуля")

    # Утверждённая логика: старт = 2 × число игроков
    start_gold = players_count * 2

    return change_house_gold(
        db,
        house=house,
        amount=start_gold,
        operation_type="grant_start",
        source_type="house_setup",
        source_id=house.id,
        reason=f"Стартовое золото дома: 2 × {players_count} игроков",
        comment="Инициализация дома",
    )


def grant_gold_from_check(
    db: Session,
    *,
    house: House,
    amount_rub: int,
    check_id: Optional[int] = None,
    performed_by_player_id: Optional[int] = None,
):
    gold_amount = calculate_gold_from_check(amount_rub)

    if gold_amount <= 0:
        return None

    return change_house_gold(
        db,
        house=house,
        amount=gold_amount,
        operation_type="grant_check",
        source_type="check",
        source_id=check_id,
        reason=f"Начисление по чеку {amount_rub} ₽",
        comment="Формула: 500 ₽ = 1 золото",
        performed_by_player_id=performed_by_player_id,
    )


def apply_expedition_gold_outcome(
    db: Session,
    *,
    house: House,
    gold_delta: int,
    map_node_id: Optional[int] = None,
    reason: str = "Результат экспедиции",
    performed_by_player_id: Optional[int] = None,
):
    if gold_delta == 0:
        return None

    operation_type = "grant_expedition" if gold_delta > 0 else "spend_action"

    return change_house_gold(
        db,
        house=house,
        amount=gold_delta,
        operation_type=operation_type,
        source_type="map_node",
        source_id=map_node_id,
        reason=reason,
        performed_by_player_id=performed_by_player_id,
    )


def apply_admin_gold_adjustment(
    db: Session,
    *,
    house: House,
    gold_delta: int,
    reason: str,
    comment: Optional[str] = None,
    performed_by_player_id: Optional[int] = None,
):
    if gold_delta == 0:
        raise GoldError("gold_delta не должен быть равен нулю")

    operation_type = "admin_adjustment_in" if gold_delta > 0 else "admin_adjustment_out"

    return change_house_gold(
        db,
        house=house,
        amount=gold_delta,
        operation_type=operation_type,
        source_type="admin_tool",
        source_id=None,
        reason=reason,
        comment=comment,
        performed_by_player_id=performed_by_player_id,
    )


def spend_gold_for_action(
    db: Session,
    *,
    house: House,
    amount: int,
    reason: str,
    source_type: str = "action",
    source_id: Optional[int] = None,
    performed_by_player_id: Optional[int] = None,
):
    if amount <= 0:
        raise GoldError("Списание золота должно быть больше нуля")

    return change_house_gold(
        db,
        house=house,
        amount=-amount,
        operation_type="spend_action",
        source_type=source_type,
        source_id=source_id,
        reason=reason,
        performed_by_player_id=performed_by_player_id,
    )


def resolve_pvp_gold(
    db: Session,
    *,
    house_a: House,
    house_b: House,
    winner_house: House,
    duel_id: int,
    stake_gold: int = 3,
    performed_by_player_id: Optional[int] = None,
):
    """
    Утверждённая схема:
    A ставит 3
    B ставит 3
    банк 6
    комиссия системы 1
    победитель получает 5
    """
    if winner_house.id not in {house_a.id, house_b.id}:
        raise GoldError("winner_house должен быть либо house_a, либо house_b")

    try:
        stake = int(stake_gold)
    except (TypeError, ValueError) as exc:
        raise GoldError("stake_gold должен быть целым числом") from exc

    if stake <= 0:
        raise GoldError("stake_gold должен быть больше нуля")

    prize = stake * 2 - 1

    change_house_gold(
        db,
        house=house_a,
        amount=-stake,
        operation_type="spend_pvp_stake",
        source_type="pvp_duel",
        source_id=duel_id,
        reason="Ставка дома в PvP",
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=house_b.id,
    )

    change_house_gold(
        db,
        house=house_b,
        amount=-stake,
        operation_type="spend_pvp_stake",
        source_type="pvp_duel",
        source_id=duel_id,
        reason="Ставка дома в PvP",
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=house_a.id,
    )

    loser_house = house_b if winner_house.id == house_a.id else house_a

    win_result = change_house_gold(
        db,
        house=winner_house,
        amount=prize,
        operation_type="pvp_win",
        source_type="pvp_duel",
        source_id=duel_id,
        reason=f'Выигрыш PvP против дома "{loser_house.name}"',
        performed_by_player_id=performed_by_player_id,
        counterparty_house_id=loser_house.id,
    )

    return {
        "ok": True,
        "duel_id": duel_id,
        "stake_per_house": stake,
        "prize_to_winner": prize,
        "winner_house_id": winner_house.id,
        "winner_house_name": winner_house.name,
        "winner_balance_after": win_result.balance_after,
        "system_fee": 1,
    }


def get_house_gold_analytics(db: Session, house_id: int):
    transactions = (
        db.query(HouseGoldTransaction)
        .filter(HouseGoldTransaction.house_id == house_id)
        .order_by(HouseGoldTransaction.created_at.asc(), HouseGoldTransaction.id.asc())
        .all()
    )

    earned_total = 0
    spent_total = 0
    by_operation_type = {}

    for tx in transactions:
        if tx.amount > 0:
            earned_total += tx.amount
        else:
            spent_total += abs(tx.amount)

        by_operation_type.setdefault(tx.operation_type, {
            "count": 0,
            "net": 0,
            "income": 0,
            "expense": 0,
        })

        bucket = by_operation_type[tx.operation_type]
        bucket["count"] += 1
        bucket["net"] += tx.amount

        if tx.amount > 0:
            bucket["income"] += tx.amount
        else:
            bucket["expense"] += abs(tx.amount)

    return {
        "transactions_count": len(transactions),
        "earned_total": earned_total,
        "spent_total": spent_total,
        "net_total": earned_total - spent_total,
        "by_operation_type": by_operation_type,
    }
