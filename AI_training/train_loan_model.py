import pandas as pd
from sklearn.model_selection import train_test_split

df = pd.read_csv('DATA/synthetic_loan_data.csv')

# print(df.shape)
# print(df.describe())
# print(df.head())
#print(df.columns.to_list())

feature_cols = ['monthly_income', 'monthly_expenses', 'existing_debt_payment', 'credit_score', 'age', 'debt_to_income_ratio', 'max_affordable_loan']

X = df[feature_cols]
y = df['max_affordable_loan']
print(X.shape)
print(y.shape)










