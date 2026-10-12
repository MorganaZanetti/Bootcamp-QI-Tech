import uuid
from datetime import date as DateType
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import String, ForeignKey, Numeric, Date, DateTime, CheckConstraint, UniqueConstraint, JSON, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClientCategory(Base):
    __tablename__ = "client_category"
    __table_args__ = (CheckConstraint("code IN ('PF','PJ')"), CheckConstraint("min_investment >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    min_investment: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))


class Client(Base):
    __tablename__ = "client"
    id: Mapped[int] = mapped_column(primary_key=True)
    client_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    category_id: Mapped[int] = mapped_column(ForeignKey("client_category.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class NaturalPerson(Base):
    __tablename__ = "natural_person"
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"), primary_key=True)
    cpf: Mapped[str] = mapped_column(String(11), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    birth_date: Mapped[DateType] = mapped_column(Date, nullable=False)


class LegalEntity(Base):
    __tablename__ = "legal_entity"
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"), primary_key=True)
    cnpj: Mapped[str] = mapped_column(String(14), unique=True, nullable=False)
    legal_name: Mapped[str] = mapped_column(String(180), nullable=False)


class Manager(Base):
    __tablename__ = "manager"
    id: Mapped[int] = mapped_column(primary_key=True)
    manager_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)


class AccountStatus(Base):
    __tablename__ = "account_status"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)


class Account(Base):
    __tablename__ = "account"
    __table_args__ = (CheckConstraint("account_type IN ('checking','investment')"), CheckConstraint("balance >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    account_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("account_status.id"), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False)
    agency: Mapped[str] = mapped_column(String(10), nullable=False, default="0001")
    account_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))


class AccountStatusHistory(Base):
    __tablename__ = "account_status_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("account_status.id"), nullable=False)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("manager.id"), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Currency(Base):
    __tablename__ = "currency"
    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class FxRate(Base):
    __tablename__ = "fx_rate"
    __table_args__ = (UniqueConstraint("currency_code", "quoted_at"), CheckConstraint("buy_rate > 0"), CheckConstraint("sell_rate > 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    fx_rate_uuid: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    buy_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    sell_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)
    quoted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CdiRate(Base):
    __tablename__ = "cdi_rate"
    date: Mapped[DateType] = mapped_column(Date, primary_key=True)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)


class InvestmentFund(Base):
    __tablename__ = "investment_fund"
    id: Mapped[int] = mapped_column(primary_key=True)
    fund_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), nullable=False)


class Position(Base):
    __tablename__ = "position"
    __table_args__ = (UniqueConstraint("account_id", "fund_id"), CheckConstraint("quantity_fx >= 0"), CheckConstraint("cost_basis_brl >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    fund_id: Mapped[int] = mapped_column(ForeignKey("investment_fund.id"), nullable=False)
    quantity_fx: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False, default=Decimal("0"))
    cost_basis_brl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))


class InvestOrder(Base):
    __tablename__ = "invest_order"
    __table_args__ = (CheckConstraint("side IN ('buy','sell')"), CheckConstraint("amount_brl > 0"), CheckConstraint("amount_fx > 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    order_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    checking_account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    investment_account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    fund_id: Mapped[int] = mapped_column(ForeignKey("investment_fund.id"), nullable=False)
    fx_rate_id: Mapped[int] = mapped_column(ForeignKey("fx_rate.id"), nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    amount_brl: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    amount_fx: Mapped[Decimal] = mapped_column(Numeric(24, 8), nullable=False)
    costs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class Entry(Base):
    __tablename__ = "entry"
    __table_args__ = (CheckConstraint("amount <> 0"), CheckConstraint("balance_after >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"), nullable=False)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("invest_order.id"), nullable=True)
    entry_type: Mapped[str] = mapped_column(String(30), nullable=False, default="transaction")
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    balance_after: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class QuoteAlert(Base):
    __tablename__ = "quote_alert"
    __table_args__ = (CheckConstraint("target_rate > 0"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"), nullable=False)
    currency_code: Mapped[str] = mapped_column(ForeignKey("currency.code"), nullable=False)
    target_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False)


class Event(Base):
    __tablename__ = "event"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_key: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), unique=True, nullable=False, default=new_uuid)
    account_id: Mapped[int | None] = mapped_column(ForeignKey("account.id"), nullable=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("invest_order.id"), nullable=True)
    request_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class FeeRule(Base):
    __tablename__ = "fee_rule"
    __table_args__ = (CheckConstraint("kind IN ('IR','IOF','spread','fee')"), CheckConstraint("rate >= 0"))
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
