import pandas as pd
import joblib

from calculations.loans import calculate_monthly_payment

model = joblib.load('AI_model/loan_amount_model.pkl')

def predict_max_loan(monthly_income, monthly_expenses, existing_debt_payment, credit_score, age):
    debt_to_income_ratio = (monthly_expenses + existing_debt_payment) / monthly_income

    input_data = pd.DataFrame([{
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "existing_debt_payment": existing_debt_payment,
        "credit_score": credit_score,
        "age": age,
        "debt_to_income_ratio": debt_to_income_ratio
    }])

    predicted_amount = model.predict(input_data)[0]
    return round(predicted_amount, 2)


def plan_goal_with_loan(gap, max_borrowable, loan_rate=9.0, loan_term_years=5):
    """
    Checks whether the predicted max loan covers the gap, and if so,
    calculates the monthly repayment for a standard term.
    """
    if gap <= 0:
        return {"loan_needed": False}

    if max_borrowable < gap:
        return {
            "loan_needed": True,
            "covers_gap": False,
            "shortfall_even_with_loan": round(gap - max_borrowable, 2)
        }

    monthly_repayment = calculate_monthly_payment(gap, loan_rate, loan_term_years)
    return {
        "loan_needed": True,
        "covers_gap": True,
        "loan_amount_needed": gap,
        "monthly_repayment": monthly_repayment,
        "loan_term_years": loan_term_years
    }








