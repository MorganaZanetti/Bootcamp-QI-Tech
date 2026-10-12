def test_register_and_login(client):
    payload={"email":"orlando@example.com","password":"senha123","cpf":"52998224725","full_name":"Orlando Teste","birth_date":"2000-01-01"}
    response=client.post("/v1/auth/register/natural-person",json=payload)
    assert response.status_code==201
    login=client.post("/v1/auth/login",json={"document":"52998224725","password":"senha123"})
    assert login.status_code==200
    assert "access_token" in login.json()

def test_reject_invalid_cpf(client):
    response=client.post("/v1/auth/register/natural-person",json={"email":"x@x.com","password":"senha123","cpf":"11111111111","full_name":"Teste","birth_date":"2000-01-01"})
    assert response.status_code==400
