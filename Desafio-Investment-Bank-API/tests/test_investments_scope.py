from src.models import Event
def setup_client(client):
    client.post("/v1/auth/register/natural-person", json={"email":"invest@a.com","password":"senha123","cpf":"52998224725","full_name":"Investidor","birth_date":"2000-01-01"})
    token = client.post("/v1/auth/login", json={"document":"52998224725","password":"senha123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    checking = client.get("/v1/accounts", headers=headers).json()[0]["account_number"]
    client.post(f"/v1/accounts/{checking}/deposits", json={"amount":"10000.00"}, headers=headers)
    investment = client.post("/v1/accounts/investment", headers=headers).json()["account_number"]
    client.post(f"/v1/manager/investment-accounts/{investment}/approve", headers={"X-Manager-Key":"manager123"})
    return headers, checking, investment


def test_metrics_have_three_currencies_and_spread(client):
    headers, _, _ = setup_client(client)
    response = client.get("/v1/investments/metrics", params={"amount_brl":"2000"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert {x["currency_code"] for x in data} == {"USD", "EUR", "JPY"}
    assert all(str(x["spread_rate"]) in ("0.025", "0.0250") for x in data)
    assert all(float(x["minimum_investment_brl"]) == 2000.0 for x in data)


def test_pf_minimum_investment(client):
    headers, checking, investment = setup_client(client)
    response = client.post("/v1/investments/applications", params={"checking_account_key":checking,"investment_account_key":investment}, json={"fund_key":"USD","amount_brl":"1999.99"}, headers=headers)
    assert response.status_code == 400
    assert "2000" in response.json()["detail"]


def test_investment_statement_and_simulation_not_stored(client, db):
    headers, checking, investment = setup_client(client)
    applied = client.post("/v1/investments/applications", params={"checking_account_key":checking,"investment_account_key":investment}, json={"fund_key":"USD","amount_brl":"2000.00"}, headers=headers)
    assert applied.status_code == 201
    assert "order_key" not in applied.json()
    statement = client.get(f"/v1/investments/statement/{investment}", headers=headers)
    assert statement.status_code == 200
    assert "totals" in statement.json()
    before_events = db.query(Event).count()
    simulation = client.post(f"/v1/investments/simulation/{investment}", json={"target_brl":"5000.00","monthly_contribution_brl":"0"}, headers=headers)
    assert simulation.status_code == 200
    assert simulation.json()["stored"] is False
    assert db.query(Event).count() == before_events


def test_currency_drop_alert_is_informative(client, monkeypatch):
    from src.connectors.market_data import MarketDataConnector
    headers, checking, investment = setup_client(client)
    applied = client.post("/v1/investments/applications", params={"checking_account_key":checking,"investment_account_key":investment}, json={"fund_key":"USD","amount_brl":"2000.00"}, headers=headers)
    assert applied.status_code == 201
    low_market = {
        "quoted_at": "2026-10-12T12:00:00+00:00",
        "fx": {
            "USD": {"buy_rate":"4.00","sell_rate":"4.05"},
            "EUR": {"buy_rate":"6.05","sell_rate":"6.12"},
            "JPY": {"buy_rate":"0.0340","sell_rate":"0.0345"},
        },
        "cdi":"0.1490","selic":"0.1500","ir":"0.1500","iof":"0.0038",
    }
    monkeypatch.setattr(MarketDataConnector, "market_data", lambda self: low_market)
    positions = client.get(f"/v1/investments/positions/{investment}", headers=headers).json()
    usd = next(item for item in positions if item["currency_code"] == "USD")
    assert usd["currency_alert"] is True
    assert "Você decide" in usd["alert_message"]
