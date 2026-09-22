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


def amortisation_schedule(principal, annual_rate, term_years):
    """
    Returns month-by-month breakdown of interest vs principal paid.
    """
    monthly_rate = annual_rate / 100 / 12
    n_months = term_years * 12
    monthly_payment = calculate_monthly_payment(principal, annual_rate, term_years)

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