# payment.py – модуль оплаты для Telegram‑бота виртуальных карт
# ---------------------------------------------------------------------
# Здесь реализованы три способа пополнения баланса карты через:
#   1️⃣ СБП (Система быстрых платежей)
#   2️⃣ ЮKassa (YooMoney) – онлайн‑оплата банковскими картами
#   3️⃣ Криптовалютные платежи (USDT, BTC) через сторонний провайдер
#
# Модуль построен как «чистый» слой бизнес‑логики – без привязки к Aiogram.
# Бот будет импортировать функции из этого файла и вызывать их из хэндлеров.
# ---------------------------------------------------------------------

import abc
import hashlib
import json
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    """Статусы платежа, возвращаемые провайдерами."""
    SUCCESS = "success"
    PENDING = "pending"
    FAILED = "failed"

@dataclass
class PaymentResult:
    """Результат обработки платежа.

    Attributes:
        status: Финальный статус (SUCCESS, PENDING, FAILED).
        transaction_id: Идентификатор транзакции у провайдера.
        amount_usd: Сумма в USD (для дальнейшего пересчёта в RUB).
        raw_response: Полный ответ провайдера (для логов).
    """
    status: PaymentStatus
    transaction_id: str
    amount_usd: float
    raw_response: Dict[str, Any]

class BasePaymentProvider(abc.ABC):
    @abc.abstractmethod
    def create_payment(self, amount_usd: float, description: str) -> PaymentResult:
        raise NotImplementedError

class SBPPaymentProvider(BasePaymentProvider):
    def __init__(self, merchant_id: str, api_key: str, callback_url: str):
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.callback_url = callback_url

    def _sign_payload(self, payload: dict) -> str:
        payload_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256((payload_json + self.api_key).encode()).hexdigest()

    def create_payment(self, amount_usd: float, description: str) -> PaymentResult:
        amount_rub = round(amount_usd * 75, 2)
        payload = {
            "merchant_id": self.merchant_id,
            "amount": amount_rub,
            "currency": "RUB",
            "description": description,
            "callback_url": self.callback_url,
        }
        payload["signature"] = self._sign_payload(payload)
        logger.debug("SBP payload: %s", payload)
        fake_response = {
            "status": "pending",
            "transaction_id": f"sbp-{hashlib.sha1(payload['description'].encode()).hexdigest()[:8]}",
            "payment_url": "https://bank.example/sbp/pay?tx=...",
        }
        status = PaymentStatus.PENDING if fake_response["status"] == "pending" else PaymentStatus.FAILED
        return PaymentResult(status, fake_response["transaction_id"], amount_usd, fake_response)

class YooKassaPaymentProvider(BasePaymentProvider):
    def __init__(self, shop_id: str, secret_key: str, return_url: str):
        self.shop_id = shop_id
        self.secret_key = secret_key
        self.return_url = return_url

    def create_payment(self, amount_usd: float, description: str) -> PaymentResult:
        fake_response = {
            "status": "pending",
            "id": f"yoo-{hashlib.sha256(description.encode()).hexdigest()[:10]}",
            "confirmation": {"url": "https://money.yoo.ru/payments/..."},
        }
        status = PaymentStatus.PENDING if fake_response["status"] == "pending" else PaymentStatus.FAILED
        return PaymentResult(status, fake_response["id"], amount_usd, fake_response)

class CryptoPaymentProvider(BasePaymentProvider):
    def __init__(self, api_key: str, api_secret: str, callback_url: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.callback_url = callback_url

    def create_payment(self, amount_usd: float, description: str) -> PaymentResult:
        amount_usdt = amount_usd
        fake_address = "0x" + hashlib.sha256(description.encode()).hexdigest()[:40]
        fake_response = {
            "status": "pending",
            "address": fake_address,
            "amount": amount_usdt,
            "currency": "USDT",
            "transaction_id": f"crypto-{hashlib.sha1(fake_address.encode()).hexdigest()[:8]}",
        }
        return PaymentResult(PaymentStatus.PENDING, fake_response["transaction_id"], amount_usd, fake_response)

def get_provider(provider_name: str) -> BasePaymentProvider:
    if provider_name == "sbp":
        return SBPPaymentProvider("YOUR_MERCHANT_ID", "YOUR_API_KEY", "https://your.domain/api/sbp/callback")
    if provider_name == "yookassa":
        return YooKassaPaymentProvider("YOUR_SHOP_ID", "YOUR_SECRET_KEY", "https://your.domain/api/yookassa/return")
    if provider_name == "crypto":
        return CryptoPaymentProvider("YOUR_CRYPTO_API_KEY", "YOUR_CRYPTO_API_SECRET", "https://your.domain/api/crypto/callback")
    raise ValueError("Unsupported provider")

async def handle_payment(event, provider_name: str, amount_usd: float, description: str):
    provider = get_provider(provider_name)
    result = provider.create_payment(amount_usd, description)
    if result.status == PaymentStatus.PENDING:
        payment_url = result.raw_response.get("payment_url") or result.raw_response.get("confirmation", {}).get("url")
        await event.answer(f"✅ Платёж создан. Перейди по ссылке: {payment_url}\nID: {result.transaction_id}")
    elif result.status == PaymentStatus.SUCCESS:
        await event.answer("✅ Пополнение успешно!")
    else:
        await event.answer("❌ Платёж не удался.")

# Дальнейшее расширение: webhook‑обработчики, БД, логирование.
