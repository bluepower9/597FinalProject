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
    if len(pw) > 16 or len(pw) < 8:
        return False
    



def validate_email(email: str) -> bool:
    '''
    Checks if a valid email was given using regex.

    Returns True if valid False if not.
    '''

    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if len(email) > 64:
        return False
    
    return re.search(regex, email) is not None



# def login_user(params: OAuth2PasswordRequestForm) -> str:
#     '''
#     Takes in user credentials (username, password) and tries to authenticate
#     and create session key.

#     Returns session key if user is authenticated, None otherwise.
#     '''
#     user = authenticate_user(params)
#     if user:
#         logging.info(f'Invalid credentials for user: {params.username}')
#         return None
    
#     logging.info(f'Generating session id for user: {params.username}')
#     sessionid = str(uuid.uuid4())

#     user = get_user_info(params.username)
#     if not add_session(sessionid, user.userid):
#         return None
    
#     return sessionid

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


