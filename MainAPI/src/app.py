import sqlalchemy
from sqlalchemy import create_engine, text
from util.util import *
from util.modelparams import *
from util.db import MySQLDatabase
import bcrypt
import uuid


database = MySQLDatabase()


def register_user(params:RegisterUser) -> bool:
    '''
    Wrapper function to perform full registering a new user sequence.

    Returns if a new user was registered or not.
    '''
    params.username = params.username.lower().strip()
    params.email = params.email.lower().strip()

    if not check_existing_user(params.username, params.email):
        result = create_new_user(params)

        logging.info(f'Successfully registered new user (username: {params.username}, email: {params.email})')
    
    else:
        logging.info(f'User already exists (username: {params.username}, email: {params.email})')
        return False
    
    return result


def login_user(params: LoginUser) -> str:
    '''
    Takes in user credentials (username, password) and tries to authenticate
    and create session key.

    Returns session key if user is authenticated, None otherwise.
    '''
    if not authenticate_user(params):
        logging.info(f'Invalid credentials for user: {params.username}')
        return None
    
    logging.info(f'Generating session id for user: {params.username}')
    sessionid = str(uuid.uuid4())

    user = get_user_info(params)
    if not add_session(sessionid, user.userid):
        return None
    
    return sessionid
        

def add_session(sessionid: str, userid) -> bool:
    db = database.db

    try:
        with db.connect() as conn:
            logging.info(f'Adding session for user_id: {userid}')
            query = text('INSERT INTO login_sessions (user_id, session_id) VALUES(:userid, :sessionid);')
            conn.execute(query, userid= userid, sessionid=sessionid)
            
    except Exception as e:
        logging.info(f'Failed to add session. Error: {e}')
        return False
    
    return True


def authenticate_user(params: UserInfo) -> bool:
    '''
    Pulls user data and performs password validation.

    Returns if the supplied password matches the stored one in database.
    '''
    user = get_user_info(params)

    if user is None:
        return False
    
    password = params.password.encode('utf-8')
    hash = bcrypt.hashpw(password, user.salt)
    
    return hash == user.password


def get_user_info(params: LoginUser) -> UserInfo:
    '''
    Fetches user info for a given username and returns all information for a user.
    Returns None if user does not exist.
    '''
    db = database.db
    user = None
    colnames = ['userid', 'username', 'email', 'password', 'salt']

    try:
        with db.connect() as conn:
            query = text('SELECT * FROM users WHERE username = :username;')
            result = conn.execute(query, username=params.username)
            result = result.fetchone()
            if result:
                user = UserInfo(**dict(zip(colnames, result)))

    except Exception as e:
        logging.error(f'Failed to fetch user info for "{params.username}"  Error: {e}')

    return user



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
            conn.execute(query, username=params.username, email=params.email, password=hash, salt=salt)

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
        query = text('SELECT * from users WHERE username = :username OR email = :email;')
        result = conn.execute(query, username=username, email=email)
        result = result.fetchall()

    return len(result) > 0


