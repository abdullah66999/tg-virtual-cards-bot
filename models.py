# models.py – SQLAlchemy модели для SQLite
# ------------------------------------------------------------
# Здесь описаны основные сущности проекта:
#   * User – пользователь Telegram (id, username, created_at)
#   * Card – виртуальная карта, привязанная к пользователю
#   * Transaction – платежи/пополнения баланса карты
#
# Для простоты используем SQLite (файл `app.db` в корне репозитория).
# В реальном продакшене рекомендуется PostgreSQL и Alembic миграции.
# ------------------------------------------------------------

import datetime as dt
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)                 # внутренний ID в базе
    tg_id = Column(Integer, unique=True, nullable=False)  # Telegram user_id
    username = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    # отношения
    cards = relationship("Card", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} tg_id={self.tg_id} username={self.username}>"

class Card(Base):
    __tablename__ = "cards"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pan = Column(String(19), unique=True, nullable=False)   # номер карты
    cvv = Column(String(4), nullable=False)
    exp_date = Column(String(7), nullable=False)            # MM/YYYY
    balance_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=dt.datetime.utcnow)

    owner = relationship("User", back_populates="cards")
    transactions = relationship("Transaction", back_populates="card", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Card id={self.id} pan={self.pan[:6]}... user_id={self.user_id}>"

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    amount_usd = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)  # success / pending / failed
    provider = Column(String(20), nullable=False)  # sbp / yookassa / crypto
    external_tx_id = Column(String(64), nullable=True)  # ID у провайдера
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    raw_data = Column(Text, nullable=True)  # JSON с ответом провайдера (для отладки)

    card = relationship("Card", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction id={self.id} card_id={self.card_id} amount={self.amount_usd} status={self.status}>"

# Helper: create engine & session (used by the bot)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///app.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    """Создать все таблицы, если они ещё не существуют."""
    Base.metadata.create_all(bind=engine)

# При импорте модуля можно сразу инициализировать БД (для простоты прототипа)
init_db()
