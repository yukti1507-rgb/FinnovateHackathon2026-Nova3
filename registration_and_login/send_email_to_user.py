import smtplib
import streamlit as st
from email.message import EmailMessage
import random
import time

Email_address = "ilafoogooa@gmail.com"
Email_password = "ltqj apmw cgyt zrqe"

def send_resetpass_email(to_email, token):
    """"Email sent to user to reset their password"""
    #st.secrets was previously used because the gmail account generates a password to be able to send emails to user 
    # sender_email = st.secrets["EMAIL_ADDRESS"]
    # sender_password = st.secrets["EMAIL_APP_PASSWORD"]
    sender_email = Email_address
    sender_password = Email_password

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
    # sender_email = st.secrets["EMAIL_ADDRESS"]
    # sender_password = st.secrets["EMAIL_APP_PASSWORD"]
    sender_email = Email_address
    sender_password = Email_password

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

def OTP_initialisation(user_email):
    """ Sending the user the email with OTP """
    #calling the otp generation function
    otp = generate_OTP()
    st.session_state["otp_code"] = otp
    st.session_state["otp_email"] = user_email
    #otp code has to expire after 5 minutes
    st.session_state["otp_expires_at"] = time.time() + 5 * 60  
    st.session_state["otp_attempts"] = 0
    #calling the send_OTP_email along with the otp to the users email
    return send_OTP_email(user_email, otp)

def OTP_verification(user_input):
    """ Checks if the OTP entered is the one that was sent to user"""
    stripped_input = user_input.strip()
    if not stripped_input.isdigit():
        message = "Only integers should be entered"
        return False, message
    elif len(stripped_input) != 6:
        message = "Otp should be 6 digits"
        return False, message
    elif "otp_code" not in st.session_state:
        message = "No otp was generated"
        return False, message
    elif time.time() > float(st.session_state["otp_expires_at"]):
        message = "OTP has expired"
        return False, message
    st.session_state["otp_attempts"] += 1
    if st.session_state["otp_attempts"] > 3:
        message = "Wrong otp has been entered too many times. Please request another otp"
        return False, message
    #remove white space before checking if it is the same as the otp code
    #.strip() returns a string so we have to force a type cast for the session state
    if stripped_input == str(st.session_state["otp_code"]):
        #resetting the session states
        st.session_state["otp_code"] = None
        st.session_state["otp_email"] = None
        st.session_state["otp_expires_at"] = None
        st.session_state["otp_attempts"] = 0
        message = "Verified"
        return True, message
    else:
        message = "Incorrect code. Please try again."
        return False, message


def main():
    generate_OTP()

if __name__ == "__main__":
    main()