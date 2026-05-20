from fastapi import APIRouter, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.house import House
from app.models.house_gold_transaction import HouseGoldTransaction
from app.services.gold_service import (
    GoldError,
    GoldInsufficientFundsError,
    change_house_gold,
    grant_gold_from_check,
    apply_expedition_gold_outcome,
    spend_gold_for_action,
    resolve_pvp_gold,
    get_house_gold_analytics,
)

router = APIRouter(prefix="/gold", tags=["gold"])


@router.post("/houses/{house_id}/grant")
def grant_gold(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        amount = int(payload.get("amount", 0))
        reason = str(payload.get("reason", "")).strip() or "Ручное начисление золота"
        source_type = str(payload.get("source_type", "manual")).strip()
        source_id = payload.get("source_id")
        comment = payload.get("comment")
        performed_by_player_id = payload.get("performed_by_player_id")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount должен быть больше нуля")

        result = change_house_gold(
            db,
            house=house,
            amount=amount,
            operation_type="grant_manual",
            source_type=source_type,
            source_id=source_id,
            reason=reason,
            comment=comment,
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()
        db.refresh(house)

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            },
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "transaction_id": result.transaction_id,
        }

    except GoldError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/houses/{house_id}/spend")
def spend_gold(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        amount = int(payload.get("amount", 0))
        reason = str(payload.get("reason", "")).strip() or "Ручное списание золота"
        source_type = str(payload.get("source_type", "manual")).strip()
        source_id = payload.get("source_id")
        performed_by_player_id = payload.get("performed_by_player_id")

        if amount <= 0:
            raise HTTPException(status_code=400, detail="amount должен быть больше нуля")

        result = spend_gold_for_action(
            db,
            house=house,
            amount=amount,
            reason=reason,
            source_type=source_type,
            source_id=source_id,
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()
        db.refresh(house)

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            },
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "transaction_id": result.transaction_id,
        }

    except GoldInsufficientFundsError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except GoldError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/houses/{house_id}/grant-from-check")
def grant_from_check(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        amount_rub = int(payload.get("amount_rub", 0))
        check_id = payload.get("check_id")
        performed_by_player_id = payload.get("performed_by_player_id")

        if amount_rub <= 0:
            raise HTTPException(status_code=400, detail="amount_rub должен быть больше нуля")

        result = grant_gold_from_check(
            db,
            house=house,
            amount_rub=amount_rub,
            check_id=check_id,
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()
        db.refresh(house)

        if result is None:
            return {
                "ok": True,
                "message": "Чек меньше порога начисления, золото не добавлено",
                "amount_rub": amount_rub,
                "gold_after": house.resource_gold,
            }

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
            },
            "amount_rub": amount_rub,
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "transaction_id": result.transaction_id,
        }

    except GoldError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/houses/{house_id}/apply-expedition")
def apply_expedition(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        gold_delta = int(payload.get("gold_delta", 0))
        map_node_id = payload.get("map_node_id")
        reason = str(payload.get("reason", "")).strip() or "Результат экспедиции"
        performed_by_player_id = payload.get("performed_by_player_id")

        result = apply_expedition_gold_outcome(
            db,
            house=house,
            gold_delta=gold_delta,
            map_node_id=map_node_id,
            reason=reason,
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()
        db.refresh(house)

        if result is None:
            return {
                "ok": True,
                "message": "Изменения золота нет",
                "gold_after": house.resource_gold,
            }

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
            },
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "transaction_id": result.transaction_id,
        }

    except GoldInsufficientFundsError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except GoldError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.post("/pvp/resolve")
def resolve_pvp(payload: dict = Body(...)):
    db: Session = SessionLocal()
    try:
        house_a_id = payload.get("house_a_id")
        house_b_id = payload.get("house_b_id")
        winner_house_id = payload.get("winner_house_id")
        duel_id = payload.get("duel_id")
        performed_by_player_id = payload.get("performed_by_player_id")

        if not all([house_a_id, house_b_id, winner_house_id, duel_id]):
            raise HTTPException(
                status_code=400,
                detail="Нужны поля house_a_id, house_b_id, winner_house_id, duel_id"
            )

        house_a = db.query(House).filter(House.id == house_a_id).first()
        house_b = db.query(House).filter(House.id == house_b_id).first()
        winner_house = db.query(House).filter(House.id == winner_house_id).first()

        if not house_a or not house_b or not winner_house:
            raise HTTPException(status_code=404, detail="Один или несколько домов не найдены")

        result = resolve_pvp_gold(
            db,
            house_a=house_a,
            house_b=house_b,
            winner_house=winner_house,
            duel_id=int(duel_id),
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()

        return result

    except GoldInsufficientFundsError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))
    except GoldError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/houses/{house_id}/transactions")
def get_house_transactions(house_id: int, limit: int = 50):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        rows = (
            db.query(HouseGoldTransaction)
            .filter(HouseGoldTransaction.house_id == house_id)
            .order_by(HouseGoldTransaction.created_at.desc(), HouseGoldTransaction.id.desc())
            .limit(limit)
            .all()
        )

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
                "gold": house.resource_gold,
            },
            "transactions": [
                {
                    "id": row.id,
                    "amount": row.amount,
                    "balance_before": row.balance_before,
                    "balance_after": row.balance_after,
                    "operation_type": row.operation_type,
                    "source_type": row.source_type,
                    "source_id": row.source_id,
                    "reason": row.reason,
                    "comment": row.comment,
                    "performed_by_player_id": row.performed_by_player_id,
                    "counterparty_house_id": row.counterparty_house_id,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in rows
            ],
        }
    finally:
        db.close()


@router.get("/houses/{house_id}/analytics")
def get_house_analytics(house_id: int):
    db: Session = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        if not house:
            raise HTTPException(status_code=404, detail="Дом не найден")

        analytics = get_house_gold_analytics(db, house_id)

        return {
            "ok": True,
            "house": {
                "id": house.id,
                "name": house.name,
                "gold": house.resource_gold,
            },
            "analytics": analytics,
        }
    finally:
        db.close()