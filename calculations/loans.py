import math

def calculate_monthly_payment(principal, annual_rate, term_years):
    """
    Standard amortising loan formula.
    """
    monthly_rate = annual_rate / 100 / 12
    n_months = term_years * 12

    if monthly_rate == 0:
        return principal / n_months

    payment = principal * (monthly_rate * (1 + monthly_rate) ** n_months) / \
              ((1 + monthly_rate) ** n_months - 1)
    return round(payment, 2)


def amortisation_schedule(principal, annual_rate, term_years=None, term_months=None):
    """
    Returns month-by-month breakdown of interest vs principal paid.
    Provide either term_years OR term_months (not both).
    """
    monthly_rate = annual_rate / 100 / 12

    if term_months is not None:
        n_months = term_months
    else:
        n_months = round(term_years * 12)

    monthly_payment = calculate_monthly_payment(principal, annual_rate, n_months / 12)

    balance = principal
    schedule = []

    for month in range(1, n_months + 1):
        interest_portion = balance * monthly_rate
        principal_portion = monthly_payment - interest_portion
        balance = max(0, balance - principal_portion)

        schedule.append({
            "month": month,
            "payment": monthly_payment,
            "interest_portion": round(interest_portion, 2),
            "principal_portion": round(principal_portion, 2),
            "remaining_balance": round(balance, 2)
        })

    return schedule

def months_to_repay(principal, annual_rate, monthly_payment):
    """
    Given a fixed monthly payment, calculates how many months
    until the loan is fully paid off.
    """
    monthly_rate = annual_rate / 100 / 12

    if monthly_rate == 0:
        return math.ceil(principal / monthly_payment)

    if monthly_payment <= principal * monthly_rate:
        return None  # payment doesn't cover interest — loan never gets paid off

    months = -math.log(1 - (principal * monthly_rate) / monthly_payment) / math.log(1 + monthly_rate)
    return math.ceil(months)


