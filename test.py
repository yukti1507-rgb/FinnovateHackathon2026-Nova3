import smtplib, tomllib

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

email = secrets["EMAIL_ADDRESS"]
password = secrets["EMAIL_APP_PASSWORD"]

print("Email:", repr(email))
print("Password length:", len(password))  # should be 16

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(email, password)
    print("Login OK")