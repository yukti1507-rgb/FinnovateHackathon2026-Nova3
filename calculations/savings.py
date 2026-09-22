def project_savings(starting_balance, monthly_contribution, annual_rate, months):
    """
    Simulates savings growth month by month.
    Returns a list of dicts, one per month, showing balance/interest/contributions.
    """
    monthly_rate = annual_rate / 100 / 12
    balance = starting_balance
    total_contributed = starting_balance
    history = []

    for month in range(1, months + 1):
        interest_earned = balance * monthly_rate
        balance = balance + interest_earned + monthly_contribution
        total_contributed += monthly_contribution

        history.append({
            "month": month,
            "balance": round(balance, 2),
            "interest_earned": round(interest_earned, 2),
            "total_contributed": round(total_contributed, 2)
        })

    return history