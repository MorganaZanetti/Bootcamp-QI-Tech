def test_pix_between_clients(client):
    client.post("/v1/auth/register/natural-person", json={"email":"one@a.com","password":"senha123","cpf":"52998224725","full_name":"Um","birth_date":"2000-01-01"})
    token1 = client.post("/v1/auth/login", json={"document":"52998224725","password":"senha123"}).json()["access_token"]
    h1 = {"Authorization": f"Bearer {token1}"}
    acc1 = client.get("/v1/accounts", headers=h1).json()[0]["account_number"]
    client.post(f"/v1/accounts/{acc1}/deposits", json={"amount":"500.00"}, headers=h1)

    client.post("/v1/auth/register/natural-person", json={"email":"two@a.com","password":"senha123","cpf":"11144477735","full_name":"Dois","birth_date":"2000-01-01"})
    pix = client.post(f"/v1/accounts/{acc1}/pix", json={"destination_document":"111.444.777-35","amount":"100.00"}, headers=h1)
    assert pix.status_code == 201
    assert float(pix.json()["balance"]) == 400.0
