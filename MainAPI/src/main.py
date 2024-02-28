from fastapi import FastAPI, HTTPException, Form, Response, Cookie, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Union
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import logging
import uvicorn
from util import *
from util.auth import *
from util.modelparams import *
from util.db import *
from app import *
from sqlalchemy import text
from jose import JWTError, jwt
from routers import documents

logging.basicConfig(level=logging.INFO)


app = FastAPI()
# app.add_middleware(HTTPSRedirectMiddleware)
app.include_router(documents.router)

database = MySQLDatabase()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')


@app.get(
        '/',
        summary='API test connection endpoint',
        tags=['healthcheck']
)
async def state_endpoint():
    logging.info('state = live')
    return {'message': 'Alive', 'live': True}


@app.get(
    '/testdb',
    summary='gets all tables to test if db active.',
    tags=['healthcheck']
)
async def testdb():
    db = database.db
    try:
        with db.connect() as conn:
            res = conn.execute(text('SHOW tables;'))
            tables = res.fetchall()
    
    except Exception as e:
        logging.error(f'Failed to fetch db info. error: {e}')
        return {'alive': False, 'error': str(e)}
    
    tables = [t[0] for t in tables]
    logging.info(f'Tables: {tables}')

    return {'alive': True, 'tables': tables}


@app.post(
    '/register',
    summary='endpoint for user to register to system',
    tags=['authentication'],
    dependencies=None
)
async def register_new_user(params:RegisterUser):
    logging.info('registration request')
    result, msg = register_user(params)
    
    

    return {'result': result, 'message': msg}


# @app.post(
#     '/login',
#     summary='login endpoint for users.',
#     tags=['authentication']
# )
# async def login(params: LoginUser, response: Response, cookie):
#     logging.info(f'authenticating user "{params.username}"...')
#     sessionid = login_user(params)
#     response.set_cookie(key='loginsession', secure=False, value = sessionid)

#     return {'login status': sessionid!=None}


@app.post(
        '/logout',
        summary='logout endpoint to invalidate token.',
        tags = ['authentication']
)
async def logout(token: Annotated[str, Depends(oauth2_scheme)]):
    if not token:
        logging.error('no token supplied.')
        return {'success': False, 'message': 'No token supplied.'}
    
    db = database.db
    try:
        with db.connect() as conn:
            query = text('INSERT INTO invalid_jwt_tokens (token) VALUES(:token);')
            conn.execute(query, token=token)

    except Exception as e:
        logging.error(f'Failed add to invalid_jwt_tokens table. Error: {e}')
        return {'success': False, 'message': 'Failed to invalidate token'}
    
    return {'success': True, 'message': 'Successfully logged out user.'}


@app.post(
        '/token',
        summary='gets token for user',
        tags=['authentication']
          )
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )

    access_token = create_access_token({'sub': user.username})

    return Token(access_token=access_token, token_type='bearer')
    
    
@app.get('/testauth')
async def testauth(current_user: Annotated[UserInfo, Depends(get_current_user)]):
    return current_user


if __name__ == '__main__':
    configs = read_configs(filename='./config.json')
    uvicorn.run('main:app', host=configs['server']['host'], port=configs['server']['port'], reload=True)