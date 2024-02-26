from fastapi import FastAPI, HTTPException, Form
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import logging
import uvicorn
from util import *
from util.modelparams import *
from util.db import *
from app import *
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)


app = FastAPI()
# app.add_middleware(HTTPSRedirectMiddleware)
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
    tags=['authentication']
)
async def register_new_user(params:RegisterUser):
    logging.info('registration request')
    result, msg = register_user(params)
    
    

    return {'result': result, 'message': msg}


@app.post(
    '/login',
    summary='login endpoint for users.',
    tags=['authentication']
)
async def login(params: LoginUser):
    logging.info(f'authenticating user "{params.username}"...')
    sessionid = login_user(params)

    return {'user': sessionid}

     


if __name__ == '__main__':
    configs = read_configs(filename='./config.json')
    uvicorn.run('main:app', host=configs['server']['host'], port=configs['server']['port'], reload=True)