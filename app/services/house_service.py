from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.house import House


def ensure_house_schema(engine):
    statements = [
        "ALTER TABLE houses ADD COLUMN IF NOT EXISTS is_ready BOOLEAN NOT NULL DEFAULT FALSE",
        "CREATE INDEX IF NOT EXISTS ix_houses_is_ready ON houses(is_ready)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def set_house_ready_logic(db: Session, *, invite_code: str, is_ready: bool):
    clean_invite_code = (invite_code or "").strip().upper()
    house = db.query(House).filter(House.invite_code == clean_invite_code).first()

    if not house:
        return {
            "ok": False,
            "message": "Дом не найден",
            "invite_code": clean_invite_code,
        }

    house.is_ready = bool(is_ready)
    db.add(house)
    db.commit()
    db.refresh(house)

    return {
        "ok": True,
        "invite_code": house.invite_code,
        "house_id": house.id,
        "house_name": house.name,
        "is_ready": bool(house.is_ready),
    }
