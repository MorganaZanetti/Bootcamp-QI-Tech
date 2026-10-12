def only_digits(value: str) -> str: return "".join(c for c in value if c.isdigit())
def is_valid_cpf(value: str) -> bool:
    cpf=only_digits(value)
    if len(cpf)!=11 or cpf==cpf[0]*11: return False
    for size in (9,10):
        total=sum(int(cpf[i])*(size+1-i) for i in range(size))
        digit=(total*10)%11
        if digit==10: digit=0
        if digit!=int(cpf[size]): return False
    return True
