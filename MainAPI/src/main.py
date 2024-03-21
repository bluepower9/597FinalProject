from fastapi import FastAPI, HTTPException, Form, Response, Cookie, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Union
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn
from util import *
from util.auth import *
from util.modelparams import *
from util.db import *
from app import *
from sqlalchemy import text
from jose import JWTError, jwt
from routers import documents, dialogue
import sys

logging.basicConfig(level=logging.INFO)


app = FastAPI()
origins = ['*']
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
    )
# app.add_middleware(HTTPSRedirectMiddleware)
app.include_router(documents.router)
app.include_router(dialogue.router)

database = MySQLDatabase()


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
async def register_new_user(username:str=Form(), email:str=Form(), password:str=Form()):
    logging.info('registration request')
    params = RegisterUser(username=username, email=email, password=password)
    result, msg = register_user(params)
    
    

    return {'result': result, 'message': msg}


@app.post(
    '/login',
    summary='login endpoint for users.',
    tags=['authentication']
)
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    logging.info(f'authenticating user "{form_data.username}"...')
    token = await login_for_access_token(form_data=form_data)
    userinfo = await get_current_user(token.access_token)
    userinfo = dict(userinfo)
    del userinfo['password']
    del userinfo['salt']
    return {'token':token, 'user': userinfo}


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
            conn.execute(query, dict(token=token))
            conn.commit()

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
    result = dict(current_user)
    del result['salt']
    del result['password']
    return result


if __name__ == '__main__':
    configs = read_configs(filename='./config.json')
    uvicorn.run('main:app', host=configs['server']['host'], port=configs['server']['port'], reload=True)