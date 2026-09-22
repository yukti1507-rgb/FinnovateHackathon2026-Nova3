import bcrypt

#hashed using bcrypt
def generate_hash(psw):
    byte_psw = psw.encode('utf-8')
    #it means bcrypt runs 2^12 times
    salt = bcrypt.gensalt(rounds = 12)
    #using hashed_psw instead of hash because hash could be a keyword and also it's confusing
    hashed_psw = bcrypt.hashpw(byte_psw, salt)
    return hashed_psw.decode('utf-8')

#validating hash vs password
def is_valid_hash(psw, hashed_psw):
    hashed_psw = hashed_psw.encode('utf-8')
    byte_psw = psw.encode('utf-8')
    is_valid = bcrypt.checkpw(byte_psw, hashed_psw)
    return is_valid