import sqlalchemy
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, text
from util.util import *
from util.modelparams import *
from util.db import MySQLDatabase
import bcrypt
import uuid
import re
import smtplib
from email.mime.text import MIMEText



database = MySQLDatabase()

configs = read_configs()

JWT_SECRET_KEY = configs['auth']['jwt_key']
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')



def register_user(params:RegisterUser) -> tuple[bool, str]:
    '''
    Wrapper function to perform full registering a new user sequence.

    Returns if a new user was registered or not and a status message.
    '''
    params.username = params.username.lower().strip()
    params.email = params.email.lower().strip()

    # validate email
    if not validate_email(params.email):
        logging.info(f'Invalid email supplied: {params.email}')
        return False, 'Invalid email supplied.'

    if not validate_pw(params.password):
        logging.info('Invalid password supplied.')
        return False, 'Invalid password'


    if not check_existing_user(params.username, params.email):
        result = create_new_user(params)

        logging.info(f'Successfully registered new user (username: {params.username}, email: {params.email})')
    
    else:
        logging.info(f'User already exists (username: {params.username}, email: {params.email})')
        return False, 'User already exists.'
    
    return result, 'Successfully registered new user.'


def validate_pw(pw: str) -> bool: 
    '''
    Checks if a valid pw is supplied.  Length must be less than or equal to 16.
    Must have 1 upper case, lower case, number and special character. 
    Greater than or equal to 8 characters.

    Returns True if valid, False otherwise.
    '''
    if len(pw) > 16 or len(pw) < 6:
        return False
    
    uppercase, lowercase, number, special = False, False, False, False

    for c in pw:
        if c.isupper():
            uppercase = True
        elif c.islower():
            lowercase = True
        elif c.isnumeric():
            number = True
        else:
            special = True
    
    return uppercase and lowercase and number and special
    



def validate_email(email: str) -> bool:
    '''
    Checks if a valid email was given using regex.

    Returns True if valid False if not.
    '''

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if len(email) > 64:
        return False
    
    return re.search(regex, email) is not None



def create_new_user(params: RegisterUser) -> bool:
    '''
    creates a new user and adds them to the db.
    Uses bcrypt to generate a salt and hash and stores the bytes in the database.

    Returns if it was successful or not.
    '''

    db = database.db

    # generates a random salt binary and converts the password into bytes
    bytes = params.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(bytes, salt)

    try:
        with db.connect() as conn:
            query = text('INSERT INTO users (username, email, password, salt) VALUES(:username, :email, :password, :salt);')
            conn.execute(query, dict(username=params.username, email=params.email, password=hash, salt=salt))
            conn.commit()

    except Exception as e:
        logging.error(f'Failed to add new user into database. error: {e}')
        return False
            
    
    return True


def get_user_from_email(email:str) -> UserInfo:
    '''
    Returns a user from a given email.
    '''
    db = database.db
    user = None
    colnames = ['userid', 'username', 'email', 'password', 'salt']

    try:
        with db.connect() as conn:
            query = text('SELECT * from users WHERE email=:email;')
            result = conn.execute(query, dict(email=email))
            result = result.fetchone()
            if result:
                user = UserInfo(**dict(zip(colnames, result)))
            
    except Exception as e:
        logging.error(f'Failed to add new user into database. error: {e}')
        return None

    return user



def check_existing_user(username:str, email:str) -> bool:
    '''
    Checks if the user already exists in the database given a username and email.

    Returns True if exists, False if it does not.
    '''
    username = username.lower().strip()
    email = email.lower().strip()

    db = database.db
    with db.connect() as conn:
        query = text('SELECT * from users WHERE username=:username OR email=:email;')
        result = conn.execute(query, dict(username=username, email=email))
        result = result.fetchall()

    return len(result) > 0


def update_password(userinfo: UserInfo, newpw: str):
    '''
    updates the password for a given user and generates new salt and hash for it.
    '''
    if not validate_pw(newpw):
        return False, 'Invalid password'

    userid = userinfo.userid
    salt = bcrypt.gensalt()
    newpw = newpw.encode('utf-8')

    hashedpw = bcrypt.hashpw(newpw, salt)

    db = database.db
    try:
        with db.connect() as conn:
            query = text('UPDATE users SET password=:hashedpw, salt=:salt WHERE user_id=:userid;')
            result = conn.execute(query, dict(hashedpw=hashedpw, salt=salt, userid=userid))
            conn.commit()
            return True, 'Success'

    except Exception as e:
        logging.info(f'Error updating pw for user {userid}.  Error: {e}')
        return False, 'Server Error'
    

def invalidate_token(token):
    '''
    Adds token to invalid table
    '''
    db = database.db
    try:
        with db.connect() as conn:
            query = text('INSERT INTO invalid_jwt_tokens (token) VALUES(:token);')
            conn.execute(query, dict(token=token))
            conn.commit()

    except Exception as e:
        logging.error(f'Failed add to invalid_jwt_tokens table. Error: {e}')
        return False
    
    return True


def send_reset_email(recipient, url):
    '''
    Sends the reset email and returns True or False if it sent successfully.
    '''
    sender, pw = configs['email']['email'], configs['email']['password']

    subject = "DocQA Password Reset"
    body = "Click the link below to reset your DocQA password. It will expire in 15 minutes.\n\n" + url

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(sender, pw)
            smtp_server.sendmail(sender, recipient, msg.as_string())
            return True

    except Exception as e:
        logging.info(e)
        return False
    

    
