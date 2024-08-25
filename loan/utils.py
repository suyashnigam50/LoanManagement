import math
from datetime import timedelta
from decimal import Decimal

def calculate_emis(loan_amount, interest_rate, term_period, disbursement_date, user_income):
    # Convert all the float values to Decimal for consistent arithmetic
    loan_amount = Decimal(loan_amount)
    interest_rate = Decimal(interest_rate)
    user_income = Decimal(user_income)

    monthly_interest_rate = (interest_rate / 100) / 12
    emi_amount = (loan_amount * monthly_interest_rate * Decimal(math.pow(1 + float(monthly_interest_rate), term_period))) / (Decimal(math.pow(1 + float(monthly_interest_rate), term_period)) - 1)
    
    # EMI amount must be at-most 60% of the monthly income of the User
    if emi_amount > 0.6 * (user_income / 12):
        raise ValueError("EMI amount exceeds 60% of user's monthly income.")
    
    # Calculate EMI details
    emis = []
    for i in range(1, term_period + 1):
        emi_date = disbursement_date + timedelta(days=i * 30)
        emis.append({
            "due_date": emi_date,
            "amount_due": float(emi_amount) if i != term_period else float(emi_amount + loan_amount * monthly_interest_rate * (term_period - i + 1))
        })

    return emis
