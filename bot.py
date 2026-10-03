# bot.py – базовый скелет Telegram‑бота на Aiogram 3
# ------------------------------------------------------------
# Этот файл содержит минимальную структуру бота, готовую к расширению
# под проект «Telegram‑бот виртуальных карт». Все чувствительные данные
# (токен бота, API‑ключи) вынесены в переменные окружения – их следует
# добавить в файл `.env` или настроить в системе.
# ------------------------------------------------------------

import os
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем модуль оплаты, который мы создали ранее
from payments.payment import get_provider, PaymentStatus, PaymentResult

# ------------------------------------------------------------
# Настройка логирования
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# Чтение конфигурации из окружения
# ------------------------------------------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("Переменная окружения BOT_TOKEN не найдена. Добавьте токен бота, полученный у @BotFather")

# ------------------------------------------------------------
# Инициализация бота и диспетчера
# ------------------------------------------------------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ------------------------------------------------------------
# Хэндлер «/start» – приветствие и главное меню
# ------------------------------------------------------------
@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🃏 Список карт", callback_data="list_cards")
    kb.button(text="💰 Пополнить баланс", callback_data="top_up")
    kb.button(text="📊 Статистика", callback_data="stats")
    await message.answer(
        "Привет! Я бот для работы с виртуальными картами. Выбери действие ниже:",
        reply_markup=kb.as_markup()
    )

# ------------------------------------------------------------
# Простой обработчик списка карт (заглушка)
# ------------------------------------------------------------
@dp.callback_query(F.data == "list_cards")
async def cb_list_cards(cb: CallbackQuery):
    # TODO: подключить реальную БД с картами пользователя
    await cb.message.edit_text(
        "📄 Твои виртуальные карты:\n\n1️⃣ **Visa **** 1234** – баланс 15 USD\n2️⃣ **Mastercard **** 5678** – баланс 8 USD",
        parse_mode="Markdown"
    )

# ------------------------------------------------------------
# Пополнение баланса – демонстрация выбора провайдера оплаты
# ------------------------------------------------------------
@dp.callback_query(F.data == "top_up")
async def cb_top_up(cb: CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="СБП", callback_data="pay_sbp")
    kb.button(text="ЮKassa", callback_data="pay_yookassa")
    kb.button(text="Crypto (USDT)", callback_data="pay_crypto")
    await cb.message.edit_text(
        "Выбери способ пополнения баланса:",
        reply_markup=kb.as_markup()
    )

# ------------------------------------------------------------
# Обработчики выбора провайдера оплаты
# ------------------------------------------------------------
@dp.callback_query(F.data.startswith("pay_"))
async def cb_choose_provider(cb: CallbackQuery):
    provider_map = {
        "pay_sbp": "sbp",
        "pay_yookassa": "yookassa",
        "pay_crypto": "crypto",
    }
    provider_key = provider_map[cb.data]
    # Для примера пополняем на $10
    amount_usd = 10.0
    description = f"Пополнение баланса пользователя {cb.from_user.id}"
    provider = get_provider(provider_key)
    result: PaymentResult = provider.create_payment(amount_usd, description)
    if result.status == PaymentStatus.PENDING:
        payment_url = result.raw_response.get("payment_url") or result.raw_response.get("confirmation", {}).get("url")
        await cb.message.edit_text(
            f"✅ Платёж создан. Перейди по ссылке для завершения:\n{payment_url}\n\nID транзакции: {result.transaction_id}",
            parse_mode="Markdown"
        )
    elif result.status == PaymentStatus.SUCCESS:
        await cb.message.edit_text("✅ Пополнение успешно! Ваш баланс обновлён.")
    else:
        await cb.message.edit_text("❌ Платёж не удался. Попробуй ещё раз.")

# ------------------------------------------------------------
# Запуск бота
# ------------------------------------------------------------
if __name__ == "__main__":
    dp.run_polling(bot)

# ------------------------------------------------------------
# Дальнейшие шаги:
#   • Добавить базу данных (PostgreSQL, SQLite) для хранения карт и баланса.
#   • Реализовать webhook‑обработчики, которые будут принимать статусы
#     от провайдеров (SBP, YooKassa, Crypto) и обновлять статус транзакции.
#   • Интегрировать модуль выдачи карт (issue_card) через API выбранного
#     BaaS‑провайдера.
# ------------------------------------------------------------
