from decimal import Decimal, ROUND_HALF_UP

def percentage_return(initial: Decimal, current: Decimal) -> Decimal:
    if initial == 0: return Decimal("0")
    return ((current/initial)-1)*100

def reference_currency_value(value_brl: Decimal, fx_rate: Decimal) -> Decimal:
    if fx_rate <= 0: raise ValueError("Cotação inválida.")
    return value_brl/fx_rate

def months_to_target(current_brl: Decimal, target_brl: Decimal, monthly_contribution: Decimal, monthly_rate: Decimal=Decimal("0")) -> int:
    if target_brl <= current_brl: return 0
    if monthly_contribution <= 0: raise ValueError("A contribuição mensal deve ser positiva.")
    balance=current_brl
    for month in range(1,1201):
        balance=balance*(Decimal("1")+monthly_rate)+monthly_contribution
        if balance>=target_brl: return month
    raise ValueError("Meta não atingida no horizonte da simulação.")

def break_even_fx(current_brl: Decimal, initial_reference_value: Decimal) -> Decimal:
    if initial_reference_value <= 0: raise ValueError("Valor de referência inválido.")
    return current_brl/initial_reference_value
