from src.validators import is_valid_cpf

def test_valid_cpf(): assert is_valid_cpf("529.982.247-25")
def test_invalid_cpf(): assert not is_valid_cpf("111.111.111-11")
