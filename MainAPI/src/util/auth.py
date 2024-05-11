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
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone


database = MySQLDatabase()
configs = read_configs()

JWT_SECRET_KEY = configs['auth']['jwt_key']
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 1440 #60*24 mins

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


async def get_current_user_for_pw_reset(token: Annotated[str, Depends(oauth2_scheme)]):
    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )

    if not valid_jwt_token(token):
        raise cred_exception
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        grant = payload.get('grant')

        if username is None or (grant != 'user' and grant != 'password reset'):
            logging.error('failed to fetch username from jwt payload.')
            raise cred_exception
        
    except JWTError as e:
        logging.info(f'error validating jwt token: {e}')
        raise cred_exception
    
    user = get_user_info(username)
    if not user:
        raise cred_exception
    return user


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    cred_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    
    #check if token is blacklisted
    if not valid_jwt_token(token):
        raise cred_exception

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        grant = payload.get('grant')

        if username is None or grant != 'user':
            logging.error('failed to fetch username from jwt payload.')
            raise cred_exception
        
    except JWTError as e:
        logging.info(f'error validating jwt token: {e}')
        raise cred_exception
    
    user = get_user_info(username)
    if not user:
        raise cred_exception
    return user
    

def valid_jwt_token(token: str) -> bool:
    db = database.db

    try:
        with db.connect() as conn:
            query = text('SELECT * FROM invalid_jwt_tokens WHERE token = :token;')
            result = conn.execute(query, dict(token=token))
            result = result.fetchone()
            if result:
                return False

    except Exception as e:
        logging.error(f'Failed to fetch user info for "{token}"  Error: {e}')
        return False

    return True


def create_access_token(data: dict, tok_life=ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=tok_life)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def authenticate_user(params: OAuth2PasswordRequestForm) -> UserInfo:
    '''
    Pulls user data and performs password validation.

    Returns if the supplied password matches the stored one in database.
    '''
    user = get_user_info(params.username)

    if user is None:
        return False
    
    password = params.password.encode('utf-8')
    hash = bcrypt.hashpw(password, user.salt)
    
    return user if hash == user.password else None


def get_user_info(username: str) -> UserInfo:
    '''
    Fetches user info for a given username and returns all information for a user.
    Returns None if user does not exist.
    '''
    db = database.db
    user = None
    colnames = ['userid', 'username', 'email', 'password', 'salt']

    try:
        with db.connect() as conn:
            query = text('SELECT * FROM users WHERE username=:username;')
            result = conn.execute(query, dict(username=username))
            result = result.fetchone()
            if result:
                user = UserInfo(**dict(zip(colnames, result)))

    except Exception as e:
        logging.error(f'Failed to fetch user info for "{username}"  Error: {e}')

    return user