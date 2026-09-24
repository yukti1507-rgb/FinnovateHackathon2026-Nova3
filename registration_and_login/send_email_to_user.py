import smtplib
import streamlit as st
from email.message import EmailMessage
import random
import time


def send_resetpass_email(to_email, token):
    """"Email sent to user to reset their password"""
    #st.secrets was previously used because the gmail account generates a password to be able to send emails to user 
    # sender_email = st.secrets["EMAIL_ADDRESS"]
    # sender_password = st.secrets["EMAIL_APP_PASSWORD"]


    sender_email = st.secrets["EMAIL_ADDRESS"]
    sender_password = st.secrets["EMAIL_APP_PASSWORD"]      

    reset_link = f"http://localhost:8501/?token={token}"

    msg = EmailMessage()
    msg["Subject"] = "Password Reset Request"
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(
        f"""Hello,\nWe received a request to reset your password. Click the link below to set a new password.This link expires in 15 minutes.
        {reset_link}\nIf you did not request this, you can safely ignore this email.""")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
    
def generate_OTP():
    """ Generating an OTP as a 2 step verification """
    #generates a random 6 digit number 
    OTP = random.randrange(100000, 999999)
    return OTP
    
def send_OTP_email(to_email, otp):

    sender_email = st.secrets["EMAIL_ADDRESS"]
    sender_password = st.secrets["EMAIL_APP_PASSWORD"]

    msg = EmailMessage()
    msg["Subject"] = "Login to App"
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(
        f"""Hello,\nyour one time verfication code is : {otp}. Please enter this number in the space provided on the app.
    If you are not trying to login please ignore this email. Your password may have been compromised.""") 
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def invalidate_otp_state(keep_flow_state=False):
    keys = [
        "otp_code",
        "otp_email",
        "otp_expires_at",
        "otp_attempts",
        "awaiting_otp",
        "pending_username",
        "pending_new_hash",
        "otp_verified",
        "otp_reason",
        "account_is_locked",
        "locked_username",
    ]

    if keep_flow_state:
        keys = [key for key in keys if key not in {"pending_username", "otp_reason", "account_is_locked", "locked_username"}]

    for key in keys:
        st.session_state.pop(key, None)


def OTP_initialisation(user_email):
    """ Sending the user the email with OTP """
    otp = generate_OTP()
    st.session_state["otp_code"] = otp
    st.session_state["otp_email"] = user_email
    st.session_state["otp_expires_at"] = time.time() + 5 * 60
    st.session_state["otp_attempts"] = 0
    return send_OTP_email(user_email, otp)


def OTP_verification(user_input):
    """ Checks if the OTP entered is the one that was sent to user"""
    if user_input is None:
        return False, "Please enter the 6-digit code."

    stripped_input = str(user_input).strip()
    if not stripped_input:
        return False, "Please enter the 6-digit code."
    if not stripped_input.isdigit():
        return False, "Only integers should be entered."
    if len(stripped_input) != 6:
        return False, "OTP should be 6 digits."

    otp_code = st.session_state.get("otp_code")
    otp_expires_at = st.session_state.get("otp_expires_at")

    if otp_code is None:
        invalidate_otp_state()
        return False, "No OTP was generated. Please request a new code."
    if otp_expires_at is None or time.time() > float(otp_expires_at):
        invalidate_otp_state()
        return False, "OTP has expired. Please request a new code."

    attempts = int(st.session_state.get("otp_attempts", 0)) + 1
    st.session_state["otp_attempts"] = attempts

    if attempts > 3:
        invalidate_otp_state()
        return False, "Wrong OTP entered too many times. Please request a new code."

    if stripped_input == str(otp_code):
        # Successful verification must keep the flow context needed by the
        # next step (for example, locked-account recovery needs the username
        # to reset the password before finishing the login). We clear the OTP
        # artefacts but preserve the username/route metadata for the caller.
        invalidate_otp_state(keep_flow_state=True)
        return True, "Verified"

    return False, "Incorrect code. Please try again."


def main():
    generate_OTP()

if __name__ == "__main__":
    main()