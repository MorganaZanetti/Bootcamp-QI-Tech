"""Cliente de terminal da INVESTMENT BANK API.

A CLI usa somente HTTP. Ela não acessa PostgreSQL diretamente e nunca exibe UUIDs.
"""

import os
from datetime import datetime
from decimal import Decimal, InvalidOperation

import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = 5.0


def header(title: str) -> None:
    print("\n" + "=" * 58)
    print(title.center(58))
    print("=" * 58)


def pause() -> None:
    input("\nPressione ENTER para continuar...")


def read_decimal(message: str) -> str:
    while True:
        raw_value = input(message).strip().replace(",", ".")
        try:
            value = Decimal(raw_value)
            if value <= 0:
                raise InvalidOperation
            return str(value)
        except (InvalidOperation, ValueError):
            print("Formato inválido. Exemplo válido: 1000.00")


def format_money(value) -> str:
    try:
        return f"R$ {Decimal(str(value)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def format_percent(value) -> str:
    try:
        return f"{Decimal(str(value)) * 100:.2f}%"
    except Exception:
        return str(value)


class ApiClient:
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.token: str | None = None
        self.http = httpx.Client(timeout=REQUEST_TIMEOUT)

    def close(self) -> None:
        self.http.close()

    def request(self, method: str, path: str, **kwargs):
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            response = self.http.request(method, f"{self.base_url}{path}", headers=headers, **kwargs)
        except httpx.TimeoutException:
            print("A API demorou demais para responder.")
            return None
        except httpx.RequestError:
            print("Não foi possível conectar à API. Verifique se ela está em execução.")
            return None

        if response.is_success:
            return response.json() if response.content else {}
        try:
            detail = response.json().get("detail", "Erro não informado.")
        except Exception:
            detail = response.text or "Erro não informado."
        print(f"Erro {response.status_code}: {detail}")
        return None

    def register_natural_person(self):
        header("CADASTRO - PESSOA FÍSICA")
        full_name = input("Nome completo (ex.: Maria Silva): ").strip()
        email = input("E-mail (ex.: maria@email.com): ").strip()
        cpf = input("CPF (ex.: 123.123.123-12): ").strip()
        birth_date_raw = input("Data de nascimento (ex.: 05/09/2005): ").strip()
        password = input("Senha (mínimo 8 caracteres): ").strip()
        try:
            birth_date = datetime.strptime(birth_date_raw, "%d/%m/%Y").date().isoformat()
        except ValueError:
            print("Data de nascimento inválida. Use dd/mm/aaaa.")
            return
        result = self.request("POST", "/v1/auth/register/natural-person", json={
            "email": email, "password": password, "cpf": cpf,
            "full_name": full_name, "birth_date": birth_date,
        })
        if result:
            print(result.get("message", "Cliente cadastrado com sucesso."))

    def register_legal_entity(self):
        header("CADASTRO - PESSOA JURÍDICA")
        legal_name = input("Razão social (ex.: Empresa LTDA): ").strip()
        email = input("E-mail (ex.: contato@empresa.com): ").strip()
        cnpj = input("CNPJ (ex.: 12.345.678/0001-90): ").strip()
        password = input("Senha (mínimo 8 caracteres): ").strip()
        result = self.request("POST", "/v1/auth/register/legal-entity", json={
            "email": email, "password": password, "cnpj": cnpj, "legal_name": legal_name,
        })
        if result:
            print(result.get("message", "Cliente cadastrado com sucesso."))

    def login(self) -> bool:
        header("LOGIN")
        document = input("CPF/CNPJ (ex.: 123.123.123-12): ").strip()
        password = input("Senha: ").strip()
        result = self.request("POST", "/v1/auth/login", json={"document": document, "password": password})
        if not result:
            return False
        self.token = result["access_token"]
        print("Login realizado com sucesso.")
        return True

    def list_accounts(self):
        header("MINHAS CONTAS")
        accounts = self.request("GET", "/v1/accounts")
        if accounts is None:
            return
        if not accounts:
            print("Nenhuma conta encontrada.")
            return
        for index, account in enumerate(accounts, 1):
            account_name = "Corrente" if account["type"] == "checking" else "Investimento"
            print(f"\n{index} - {account_name}")
            print(f"    Agência: {account['agency']}")
            print(f"    Conta: {account['account_number']}")
            print(f"    Status: {account['status']}")
            print(f"    Saldo: {format_money(account['balance'])}")

    def deposit(self):
        header("DEPÓSITO")
        account_key = input("Número da conta corrente (ex.: 123456): ").strip()
        amount = read_decimal("Valor a ser depositado (ex.: 1000.00): R$ ")
        result = self.request("POST", f"/v1/accounts/{account_key}/deposits", json={"amount": amount})
        if result:
            print(result["message"])
            print(f"Novo saldo: {format_money(result['balance'])}")

    def transfer(self):
        header("TRANSFERÊNCIA")
        source_key = input("Conta de origem (ex.: 123456): ").strip()
        destination_key = input("Conta de destino (ex.: 654321): ").strip()
        amount = read_decimal("Valor da transferência (ex.: 500.00): R$ ")
        result = self.request("POST", f"/v1/accounts/{source_key}/transfers", json={
            "destination_account_key": destination_key, "amount": amount,
        })
        if result:
            print(result["message"])
            print(f"Saldo da conta de origem: {format_money(result['balance'])}")

    def pix(self):
        header("PIX")
        source_key = input("Conta de origem (ex.: 123456): ").strip()
        destination_document = input("CPF/CNPJ do destinatário (ex.: 123.123.123-12): ").strip()
        amount = read_decimal("Valor do PIX (ex.: 250.00): R$ ")
        result = self.request("POST", f"/v1/accounts/{source_key}/pix", json={
            "destination_document": destination_document, "amount": amount,
        })
        if result:
            print(result["message"])
            print(f"Saldo da conta de origem: {format_money(result['balance'])}")

    def checking_statement(self):
        header("EXTRATO DA CONTA CORRENTE")
        account_number = input("Número da conta corrente (ex.: 123456): ").strip()
        statement = self.request("GET", f"/v1/accounts/{account_number}/statement")
        if statement is None:
            return
        print(f"\nAgência: {statement['agency']} | Conta: {statement['account_number']}")
        if not statement["entries"]:
            print("Nenhuma movimentação encontrada.")
        else:
            print("\nData                 Movimentação                    Valor          Saldo")
            print("-" * 78)
            for entry in statement["entries"]:
                raw_date = str(entry["created_at"]).replace("Z", "+00:00")
                try:
                    date_text = datetime.fromisoformat(raw_date).strftime("%d/%m/%Y %H:%M")
                except ValueError:
                    date_text = raw_date
                amount = Decimal(str(entry["amount"]))
                sign = "+" if amount > 0 else "-"
                value = format_money(abs(amount))
                print(f"{date_text:<20} {entry['description']:<30} {sign} {value:<12} {format_money(entry['balance_after'])}")
        print(f"\nSaldo atual: {format_money(statement['balance'])}")

    def request_investment_account(self):
        header("ABRIR CONTA DE INVESTIMENTO")
        result = self.request("POST", "/v1/accounts/investment")
        if result:
            print(result["message"])
            print(f"Número da conta: {result['account_number']}")
            print("Status: pendente de aprovação")

    def investment_metrics(self):
        header("MÉTRICAS ANTES DO INVESTIMENTO")
        amount = read_decimal("Valor que pretende investir (ex.: 2000.00): R$ ")
        metrics = self.request("GET", "/v1/investments/metrics", params={"amount_brl": amount})
        if metrics is None:
            return
        for item in metrics:
            print(f"\n--- {item['currency_code']} - {item['currency_name']} ---")
            print(f"Câmbio compra: {item['fx_buy_rate']}")
            print(f"Câmbio venda: {item['fx_sell_rate']}")
            print(f"CDI: {format_percent(item['cdi_rate'])}")
            print(f"Selic: {format_percent(item['selic_rate'])}")
            print(f"IR (referência): {format_percent(item['ir_rate'])}")
            print(f"IOF: {format_percent(item['iof_rate'])} = {format_money(item['iof_value_brl'])}")
            print(f"Spread do banco: {format_percent(item['spread_rate'])} = {format_money(item['spread_value_brl'])}")
            print(f"Valor líquido convertido: {format_money(item['net_amount_for_conversion_brl'])}")
            print(f"Quantidade estimada da moeda: {item['estimated_currency_amount']}")
            print(f"Valor mínimo permitido: {format_money(item['minimum_investment_brl'])}")

    def apply_investment(self):
        header("REALIZAR INVESTIMENTO")
        self.investment_metrics()
        print("\nMoedas disponíveis: USD (Dólar), EUR (Euro), JPY (Iene)")
        checking_key = input("Número da conta corrente (ex.: 123456): ").strip()
        investment_key = input("Número da conta de investimento (ex.: 654321): ").strip()
        fund_key = input("Moeda desejada (USD/EUR/JPY): ").strip().upper()
        amount = read_decimal("Valor da aplicação (ex.: 2000.00): R$ ")

        # Antes de confirmar uma nova aplicação, verifica se a moeda já atingiu
        # o limite de alerta. O cliente continua tendo a decisão final.
        positions = self.request("GET", f"/v1/investments/positions/{investment_key}")
        if positions is not None:
            for position in positions:
                if position["currency_code"] == fund_key and position.get("currency_alert"):
                    print("\n*** " + position["alert_message"] + " ***")
                    break

        confirm = input("Confirmar investimento? (S/N): ").strip().upper()
        if confirm != "S":
            print("Investimento cancelado pelo cliente.")
            return
        result = self.request("POST", "/v1/investments/applications",
            params={"checking_account_key": checking_key, "investment_account_key": investment_key},
            json={"fund_key": fund_key, "amount_brl": amount})
        if result:
            print(result["message"])
            print(f"Número da ordem: {result['order_id']}")

    def investment_positions(self):
        header("MEUS INVESTIMENTOS")
        investment_key = input("Número da conta de investimento (ex.: 654321): ").strip()
        positions = self.request("GET", f"/v1/investments/positions/{investment_key}")
        if positions is None:
            return
        if not positions:
            print("Você ainda não possui investimentos.")
            return
        for position in positions:
            print(f"\n{position['currency_code']} - {position['fund_name']}")
            print(f"Quantidade na moeda: {position['quantity_fx']}")
            print(f"Total aplicado: {format_money(position['cost_basis_brl'])}")
            print(f"Valor atual: {format_money(position['current_value_brl'])}")
            print(f"Ganho/perda em real: {format_money(position['profit_loss_brl'])}")
            print(f"Ganho/perda na moeda: {position['profit_loss_fx']} {position['currency_code']}")
            print(f"Cotação atual: {position['current_fx_rate']}")
            print(f"Limite mínimo de alerta: {position['alert_limit_fx']}")
            if position.get("currency_alert"):
                print("\n*** " + position["alert_message"] + " ***")

    def investment_statement(self):
        header("EXTRATO DE INVESTIMENTOS")
        investment_key = input("Número da conta de investimento (ex.: 654321): ").strip()
        statement = self.request("GET", f"/v1/investments/statement/{investment_key}")
        if statement is None:
            return
        if not statement["entries"]:
            print("Nenhuma movimentação de investimento encontrada.")
            return
        for entry in statement["entries"]:
            print(f"\nOrdem #{entry['order_id']} | {entry['currency_code']} | {entry['created_at']}")
            print(f"Valor aplicado: {format_money(entry['amount_brl'])}")
            print(f"Spread: {format_money(entry['spread_brl'])}")
            print(f"IOF: {format_money(entry['iof_brl'])}")
            print(f"IR (taxa de referência): {format_percent(entry['ir_rate'])}")
            print(f"CDI: {format_percent(entry['cdi_rate'])}")
            print(f"Selic: {format_percent(entry['selic_rate'])}")
            print(f"Valor líquido investido: {format_money(entry['net_invested_brl'])}")
            print(f"Valor atual: {format_money(entry['current_value_brl'])}")
            print(f"Ganho/perda em real: {format_money(entry['profit_loss_brl'])}")
            print(f"Ganho/perda na moeda: {entry['profit_loss_fx']} {entry['currency_code']}")
        totals = statement["totals"]
        print("\n--- TOTAL GERAL ---")
        print(f"Total aplicado: {format_money(totals['gross_invested_brl'])}")
        print(f"Total de spread: {format_money(totals['spread_brl'])}")
        print(f"Total de IOF: {format_money(totals['iof_brl'])}")
        print(f"Total de custos: {format_money(totals['total_costs_brl'])}")
        print(f"Total líquido investido: {format_money(totals['net_invested_brl'])}")

    def simulate(self):
        header("SIMULAÇÃO DE META")
        investment_key = input("Número da conta de investimento (ex.: 654321): ").strip()
        target = read_decimal("Valor meta desejado (ex.: 50000.00): R$ ")
        result = self.request("POST", f"/v1/investments/simulation/{investment_key}", json={
            "target_brl": target, "monthly_contribution_brl": "0"
        })
        if result is None:
            return
        print("\nEstimativa por moeda:")
        for item in result["by_currency"]:
            months = item["estimated_months"]
            text = f"{months} meses" if months is not None else "sem posição atual nessa moeda"
            print(f"{item['currency_code']}: atual {format_money(item['current_value_brl'])} -> {text}")
        combined = result["combined"]
        months = combined["estimated_months"]
        text = f"{months} meses" if months is not None else "não calculável sem valor investido"
        print(f"\nTodas as moedas juntas: {format_money(combined['current_value_brl'])} -> {text}")
        print(result["message"])

    def manager_pending_accounts(self, manager_key):
        header("SOLICITAÇÕES PENDENTES")
        accounts = self.request("GET", "/v1/manager/investment-accounts/pending", headers={"X-Manager-Key": manager_key})
        if accounts is None:
            return
        if not accounts:
            print("Não existem solicitações pendentes.")
            return
        for account in accounts:
            print(f"Conta: {account['account_number']} | Cliente interno: {account['client_id']} | Status: pendente")

    def manager_decide_account(self, manager_key, approve):
        header("APROVAR CONTA DE INVESTIMENTO" if approve else "REJEITAR CONTA DE INVESTIMENTO")
        account_key = input("Número da conta de investimento (ex.: 654321): ").strip()
        action = "approve" if approve else "reject"
        result = self.request("POST", f"/v1/manager/investment-accounts/{account_key}/{action}", headers={"X-Manager-Key": manager_key})
        if result:
            print(result["message"])

    def fx_rates(self):
        header("COTAÇÃO DE MOEDA")
        currency = input("Moeda (USD/EUR/JPY): ").strip().upper()
        rate = self.request("GET", f"/v1/fx-rates/{currency}")
        if rate:
            print(f"Compra: {rate['buy_rate']} | Venda: {rate['sell_rate']} | Data: {rate['quoted_at']}")


def registration_menu(api: ApiClient) -> None:
    while True:
        header("COMO VOCÊ GOSTARIA DE SE CADASTRAR?")
        print("1 - Pessoa física\n2 - Pessoa jurídica\n0 - Voltar")
        option = input("Insira a opção desejada: ").strip()
        if option == "1": api.register_natural_person(); pause()
        elif option == "2": api.register_legal_entity(); pause()
        elif option == "0": return
        else: print("Opção inválida.")


def investment_menu(api: ApiClient) -> None:
    while True:
        header("ÁREA DE INVESTIMENTOS")
        print("1 - Solicitar abertura de conta de investimento")
        print("2 - Consultar cotação")
        print("3 - Ver métricas antes de investir")
        print("4 - Meus investimentos")
        print("5 - Extrato de investimentos")
        print("6 - Realizar investimento")
        print("7 - Simular tempo para alcançar uma meta")
        print("0 - Voltar")
        option = input("Insira a opção desejada: ").strip()
        actions = {
            "1": api.request_investment_account, "2": api.fx_rates,
            "3": api.investment_metrics, "4": api.investment_positions,
            "5": api.investment_statement, "6": api.apply_investment,
            "7": api.simulate,
        }
        if option in actions: actions[option](); pause()
        elif option == "0": return
        else: print("Opção inválida.")


def authenticated_menu(api: ApiClient) -> None:
    while api.token:
        header("INVESTMENT BANK - MENU PRINCIPAL")
        print("1 - Consultar minhas contas")
        print("2 - Depositar")
        print("3 - Transferir")
        print("4 - PIX")
        print("5 - Extrato da conta corrente")
        print("6 - Investimentos")
        print("7 - Sair da conta")
        print("0 - Encerrar programa")
        option = input("Insira a opção desejada: ").strip()
        actions = {"1": api.list_accounts, "2": api.deposit, "3": api.transfer, "4": api.pix, "5": api.checking_statement, "6": lambda: investment_menu(api)}
        if option in actions:
            actions[option]()
            if option != "6": pause()
        elif option == "7": api.token = None; print("Você saiu da conta.")
        elif option == "0": api.token = None; raise SystemExit
        else: print("Opção inválida.")


def manager_menu(api: ApiClient) -> None:
    header("ACESSO DO GERENTE")
    manager_key = input("Senha/chave do gerente: ").strip()
    while True:
        header("GERENTE - CONTAS DE INVESTIMENTO")
        print("1 - Ver solicitações pendentes\n2 - Aprovar conta de investimento\n3 - Rejeitar conta de investimento\n0 - Voltar")
        option = input("Insira a opção desejada: ").strip()
        if option == "1": api.manager_pending_accounts(manager_key); pause()
        elif option == "2": api.manager_decide_account(manager_key, True); pause()
        elif option == "3": api.manager_decide_account(manager_key, False); pause()
        elif option == "0": return
        else: print("Opção inválida.")


def main() -> None:
    api = ApiClient()
    try:
        while True:
            header("INVESTMENT BANK API")
            print("1 - Login\n2 - Cadastro\n3 - Acesso do gerente\n0 - Sair")
            option = input("Insira a opção desejada: ").strip()
            if option == "1":
                if api.login(): authenticated_menu(api)
                else: pause()
            elif option == "2": registration_menu(api)
            elif option == "3": manager_menu(api)
            elif option == "0": print("Programa encerrado."); break
            else: print("Opção inválida.")
    except (KeyboardInterrupt, EOFError, SystemExit):
        print("\nPrograma encerrado.")
    finally:
        api.close()


if __name__ == "__main__":
    main()
