def auth(client):
    response = client.post("/v1/auth/register/natural-person", json={"email":"a@a.com","password":"senha123","cpf":"52998224725","full_name":"Cliente","birth_date":"2000-01-01"})
    assert response.status_code == 201
    assert "uuid" not in response.text.lower()
    assert "client_key" not in response.json()
    token = client.post("/v1/auth/login", json={"document":"52998224725","password":"senha123"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_registration_creates_open_checking_account(client):
    headers = auth(client)
    accounts = client.get("/v1/accounts", headers=headers)
    assert accounts.status_code == 200
    data = accounts.json()
    assert len(data) == 1
    assert data[0]["type"] == "checking"
    assert data[0]["status"] == "open"
    assert "account_key" not in data[0]


def test_deposit_in_automatic_checking_account(client):
    headers = auth(client)
    account = client.get("/v1/accounts", headers=headers).json()[0]
    deposit = client.post(f"/v1/accounts/{account['account_number']}/deposits", json={"amount":"100.00"}, headers=headers)
    assert deposit.status_code == 201
    assert deposit.json()["balance"] == "100.00" or float(deposit.json()["balance"]) == 100.0


def test_investment_account_request_is_pending(client):
    headers = auth(client)
    response = client.post("/v1/accounts/investment", headers=headers)
    assert response.status_code == 201
    assert response.json()["account_type"] == "investment"
    assert response.json()["status"] == "pending"
    assert "account_key" not in response.json()


def test_cannot_request_second_pending_investment_account(client):
    headers = auth(client)
    assert client.post("/v1/accounts/investment", headers=headers).status_code == 201
    assert client.post("/v1/accounts/investment", headers=headers).status_code == 409


def test_manager_can_approve_investment_account(client):
    headers = auth(client)
    requested = client.post("/v1/accounts/investment", headers=headers)
    account_number = requested.json()["account_number"]
    approved = client.post(f"/v1/manager/investment-accounts/{account_number}/approve", headers={"X-Manager-Key": "manager123"})
    assert approved.status_code == 200
    assert approved.json()["status"] == "open"
    assert "account_key" not in approved.json()


def test_manager_can_reject_investment_account(client):
    headers = auth(client)
    requested = client.post("/v1/accounts/investment", headers=headers)
    account_number = requested.json()["account_number"]
    rejected = client.post(f"/v1/manager/investment-accounts/{account_number}/reject", headers={"X-Manager-Key": "manager123"})
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "closed"


def test_checking_statement_starts_empty(client):
    headers = auth(client)
    account = client.get("/v1/accounts", headers=headers).json()[0]
    response = client.get(f"/v1/accounts/{account['account_number']}/statement", headers=headers)
    assert response.status_code == 200
    assert response.json()["entries"] == []
    assert "account_key" not in response.text


def test_checking_statement_shows_deposit(client):
    headers = auth(client)
    account = client.get("/v1/accounts", headers=headers).json()[0]
    client.post(f"/v1/accounts/{account['account_number']}/deposits", json={"amount":"150.00"}, headers=headers)
    response = client.get(f"/v1/accounts/{account['account_number']}/statement", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["balance"] == "150.00" or float(data["balance"]) == 150.0
    assert data["entries"][0]["type"] == "deposit"
    assert data["entries"][0]["description"] == "Depósito"
    assert float(data["entries"][0]["amount"]) == 150.0


def test_cannot_read_another_clients_statement(client):
    headers_a = auth(client)
    account_a = client.get("/v1/accounts", headers=headers_a).json()[0]
    client.post("/v1/auth/register/natural-person", json={"email":"b@b.com","password":"senha123","cpf":"11144477735","full_name":"Outro","birth_date":"2000-01-01"})
    token_b = client.post("/v1/auth/login", json={"document":"11144477735","password":"senha123"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    response = client.get(f"/v1/accounts/{account_a['account_number']}/statement", headers=headers_b)
    assert response.status_code == 404
