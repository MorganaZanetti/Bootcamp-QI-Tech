from decimal import Decimal
from src.controllers.investment_calculation import percentage_return,reference_currency_value,months_to_target,break_even_fx

def test_percentage_return(): assert percentage_return(Decimal("100"),Decimal("112"))==Decimal("12.00")
def test_reference_currency_value(): assert reference_currency_value(Decimal("1000"),Decimal("5"))==Decimal("200")
def test_months_to_target(): assert months_to_target(Decimal("0"),Decimal("1000"),Decimal("250"))==4
def test_break_even_fx(): assert break_even_fx(Decimal("112000"),Decimal("20000"))==Decimal("5.6")
