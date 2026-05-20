from app.database import engine, Base

# важно: импортируем все модели, чтобы Base их увидел
from app.models import *

def create_tables():
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Готово.")

if __name__ == "__main__":
    create_tables()