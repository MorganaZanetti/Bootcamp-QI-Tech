from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from src.config import settings
from src.connectors.market_data import MarketDataConnector
from src.models import Position, InvestOrder, Entry, Event, FxRate
from src.repositories.accounts import AccountRepository
from src.repositories.clients import ClientRepository
from src.repositories.investments import InvestmentRepository


MONEY = Decimal("0.01")
FX_DECIMALS = Decimal("0.00000001")


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


class InvestmentController:
    def __init__(self, db):
        self.db = db
        self.accounts = AccountRepository(db)
        self.clients = ClientRepository(db)
        self.investments = InvestmentRepository(db)
        self.connector = MarketDataConnector()

    def _validate_open_investment_account(self, client, account):
        if not account or account.client_id != client.id or account.account_type != "investment":
            raise ValueError("Conta de investimento inválida.")
        status = self.accounts.status_by_id(account.status_id)
        if not status or status.code != "open":
            raise ValueError("A conta de investimento ainda não foi aprovada pelo gerente.")

    def _market_data(self):
        try:
            return self.connector.market_data()
        except Exception as error:
            raise ValueError("Não foi possível consultar a API de dados de mercado.") from error

    def _minimum_investment(self, client):
        category = self.clients.category_for_client(client)
        return Decimal(category.min_investment)

    def metrics(self, client, amount_brl=None):
        market = self._market_data()
        minimum = self._minimum_investment(client)
        amount = Decimal(amount_brl) if amount_brl is not None else minimum
        spread_rate = settings.spread_rate
        iof_rate = Decimal(str(market["iof"]))
        ir_rate = Decimal(str(market["ir"]))
        result = []
        for fund in self.investments.funds():
            fx = market["fx"][fund.currency_code]
            sell_rate = Decimal(str(fx["sell_rate"]))
            spread_value = money(amount * spread_rate)
            iof_value = money(amount * iof_rate)
            net_amount = money(max(Decimal("0"), amount - spread_value - iof_value))
            amount_fx = (net_amount / sell_rate).quantize(FX_DECIMALS, rounding=ROUND_HALF_UP)
            result.append({
                "fund_id": fund.id,
                "currency_code": fund.currency_code,
                "currency_name": fund.name,
                "amount_brl": money(amount),
                "minimum_investment_brl": money(minimum),
                "fx_buy_rate": Decimal(str(fx["buy_rate"])),
                "fx_sell_rate": sell_rate,
                "cdi_rate": Decimal(str(market["cdi"])),
                "selic_rate": Decimal(str(market["selic"])),
                "ir_rate": ir_rate,
                "iof_rate": iof_rate,
                "spread_rate": spread_rate,
                "spread_value_brl": spread_value,
                "iof_value_brl": iof_value,
                "ir_value_brl_at_application": Decimal("0.00"),
                "net_amount_for_conversion_brl": net_amount,
                "estimated_currency_amount": amount_fx,
                "note": "IR é exibido como referência e não é descontado do principal no momento da aplicação; incide sobre eventual rendimento.",
            })
        return result

    def apply(self, client, checking_key, investment_key, fund_key, amount_brl):
        amount_brl = money(amount_brl)
        minimum = self._minimum_investment(client)
        if amount_brl < minimum:
            raise ValueError(f"Valor mínimo para investimento: R$ {minimum:.2f}.")

        checking = self.accounts.by_key(checking_key, True)
        investment = self.accounts.by_key(investment_key, True)
        fund = self.investments.fund_by_key(fund_key)
        if not checking or checking.client_id != client.id or checking.account_type != "checking":
            raise ValueError("Conta corrente inválida.")
        checking_status = self.accounts.status_by_id(checking.status_id)
        if not checking_status or checking_status.code != "open":
            raise ValueError("A conta corrente não está aberta.")
        self._validate_open_investment_account(client, investment)
        if not fund or fund.currency_code not in ("USD", "EUR", "JPY"):
            raise ValueError("Moeda de investimento inválida. Use USD, EUR ou JPY.")
        if checking.balance < amount_brl:
            raise ValueError("Saldo insuficiente.")

        market = self._market_data()
        fx = market["fx"][fund.currency_code]
        sell_rate = Decimal(str(fx["sell_rate"]))
        buy_rate = Decimal(str(fx["buy_rate"]))
        spread_value = money(amount_brl * settings.spread_rate)
        iof_rate = Decimal(str(market["iof"]))
        iof_value = money(amount_brl * iof_rate)
        net_amount = money(amount_brl - spread_value - iof_value)
        if net_amount <= 0:
            raise ValueError("O valor líquido do investimento deve ser positivo.")
        amount_fx = (net_amount / sell_rate).quantize(FX_DECIMALS, rounding=ROUND_HALF_UP)

        quoted_at = datetime.fromisoformat(str(market["quoted_at"]).replace("Z", "+00:00"))
        rate = FxRate(currency_code=fund.currency_code, buy_rate=buy_rate, sell_rate=sell_rate, quoted_at=quoted_at)
        self.db.add(rate)
        self.db.flush()

        checking.balance -= amount_brl
        investment.balance += net_amount
        position = self.investments.position(investment.id, fund.id, True)
        if not position:
            position = Position(account_id=investment.id, fund_id=fund.id, quantity_fx=Decimal("0"), cost_basis_brl=Decimal("0"))
            self.db.add(position)
        position.quantity_fx += amount_fx
        position.cost_basis_brl += amount_brl

        costs = {
            "spread_rate": str(settings.spread_rate),
            "spread_brl": str(spread_value),
            "iof_rate": str(iof_rate),
            "iof_brl": str(iof_value),
            "ir_rate": str(market["ir"]),
            "ir_brl_at_application": "0.00",
            "selic_rate": str(market["selic"]),
            "cdi_rate": str(market["cdi"]),
            "net_invested_brl": str(net_amount),
        }
        order = InvestOrder(
            checking_account_id=checking.id,
            investment_account_id=investment.id,
            fund_id=fund.id,
            fx_rate_id=rate.id,
            side="buy",
            amount_brl=amount_brl,
            amount_fx=amount_fx,
            costs=costs,
        )
        self.db.add(order)
        self.db.flush()
        self.db.add_all([
            Entry(account_id=checking.id, order_id=order.id, entry_type="investment_out", amount=-amount_brl, balance_after=checking.balance),
            Entry(account_id=investment.id, order_id=order.id, entry_type="investment_in", amount=net_amount, balance_after=investment.balance),
            Event(account_id=investment.id, order_id=order.id, detail={"type": "investment_buy", "currency": fund.currency_code}),
        ])
        self.db.commit()
        return order

    def positions(self, client, investment_key):
        account = self.accounts.by_key(investment_key)
        self._validate_open_investment_account(client, account)
        market = self._market_data()
        result = []
        for position in self.investments.positions(account.id):
            fund = self.investments.fund_by_id(position.fund_id)
            current_rate = Decimal(str(market["fx"][fund.currency_code]["buy_rate"]))
            current_brl = money(position.quantity_fx * current_rate)
            profit_brl = money(current_brl - position.cost_basis_brl)
            average_rate = Decimal(position.cost_basis_brl) / Decimal(position.quantity_fx) if position.quantity_fx else Decimal("0")
            alert_limit = (average_rate * (Decimal("1") - settings.currency_drop_alert_rate)).quantize(FX_DECIMALS)
            alert = current_rate <= alert_limit if alert_limit > 0 else False
            result.append({
                "fund_id": fund.id,
                "fund_name": fund.name,
                "currency_code": fund.currency_code,
                "quantity_fx": position.quantity_fx,
                "cost_basis_brl": position.cost_basis_brl,
                "current_fx_rate": current_rate,
                "current_value_brl": current_brl,
                "profit_loss_brl": profit_brl,
                "profit_loss_fx": (profit_brl / current_rate).quantize(FX_DECIMALS) if current_rate else Decimal("0"),
                "alert_limit_fx": alert_limit,
                "currency_alert": alert,
                "alert_message": (
                    f"ALERTA: {fund.currency_code} atingiu o limite mínimo definido (queda de 10% em relação ao custo médio). Você decide se deseja continuar investindo."
                    if alert else None
                ),
            })
        return result

    def statement(self, client, investment_key):
        account = self.accounts.by_key(investment_key)
        self._validate_open_investment_account(client, account)
        market = self._market_data()
        orders = self.investments.orders(account.id)
        rows = []
        total_gross = Decimal("0")
        total_spread = Decimal("0")
        total_iof = Decimal("0")
        total_net = Decimal("0")
        for order in orders:
            fund = self.investments.fund_by_id(order.fund_id)
            costs = order.costs or {}
            current_rate = Decimal(str(market["fx"][fund.currency_code]["buy_rate"]))
            current_brl = money(Decimal(order.amount_fx) * current_rate)
            profit_brl = money(current_brl - Decimal(order.amount_brl))
            spread = Decimal(str(costs.get("spread_brl", "0")))
            iof = Decimal(str(costs.get("iof_brl", "0")))
            net = Decimal(str(costs.get("net_invested_brl", order.amount_brl)))
            total_gross += Decimal(order.amount_brl)
            total_spread += spread
            total_iof += iof
            total_net += net
            rows.append({
                "order_id": order.id,
                "created_at": order.created_at,
                "currency_code": fund.currency_code,
                "amount_brl": order.amount_brl,
                "amount_fx": order.amount_fx,
                "spread_brl": spread,
                "iof_brl": iof,
                "ir_rate": Decimal(str(costs.get("ir_rate", market["ir"]))),
                "selic_rate": Decimal(str(costs.get("selic_rate", market["selic"]))),
                "cdi_rate": Decimal(str(costs.get("cdi_rate", market["cdi"]))),
                "net_invested_brl": net,
                "current_value_brl": current_brl,
                "profit_loss_brl": profit_brl,
                "profit_loss_fx": (profit_brl / current_rate).quantize(FX_DECIMALS) if current_rate else Decimal("0"),
            })
        return {
            "entries": rows,
            "totals": {
                "gross_invested_brl": money(total_gross),
                "spread_brl": money(total_spread),
                "iof_brl": money(total_iof),
                "net_invested_brl": money(total_net),
                "total_costs_brl": money(total_spread + total_iof),
            },
        }

    def simulate(self, client, investment_key, target_brl):
        # Somente cálculo em memória. Nada desta simulação é persistido.
        account = self.accounts.by_key(investment_key)
        self._validate_open_investment_account(client, account)
        target = Decimal(target_brl)
        market = self._market_data()
        annual_rate = Decimal(str(market["selic"])) * (Decimal("1") - Decimal(str(market["ir"])))
        monthly_rate = (Decimal("1") + annual_rate) ** (Decimal("1") / Decimal("12")) - Decimal("1")

        def months_needed(current):
            current = Decimal(current)
            if current >= target:
                return 0
            if current <= 0 or monthly_rate <= 0:
                return None
            balance = current
            for month in range(1, 1201):
                balance *= Decimal("1") + monthly_rate
                if balance >= target:
                    return month
            return None

        currencies = []
        total_current = Decimal("0")
        positions = {self.investments.fund_by_id(p.fund_id).currency_code: p for p in self.investments.positions(account.id)}
        for code in ("USD", "EUR", "JPY"):
            position = positions.get(code)
            rate = Decimal(str(market["fx"][code]["buy_rate"]))
            current = money(Decimal(position.quantity_fx) * rate) if position else Decimal("0.00")
            total_current += current
            currencies.append({
                "currency_code": code,
                "current_value_brl": current,
                "target_brl": money(target),
                "estimated_months": months_needed(current),
            })
        return {
            "target_brl": money(target),
            "reference_annual_rate": annual_rate,
            "reference_monthly_rate": monthly_rate,
            "by_currency": currencies,
            "combined": {
                "current_value_brl": money(total_current),
                "estimated_months": months_needed(total_current),
            },
            "stored": False,
            "message": "Simulação calculada em memória. Nenhum valor, cálculo ou meta foi salvo no banco de dados.",
        }
