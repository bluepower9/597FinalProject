from fastapi import FastAPI, HTTPException, Form
import logging
import uvicorn
from util import *
from util.modelparams import GPTQueryParams
from app import *

logging.basicConfig(level=logging.INFO)


app = FastAPI()

@app.get(
        '/',
        summary='API test connection endpoint',
        tags=['healthcheck']
)
async def state_endpoint():
    logging.info('state = live')
    return {'message': 'Alive', 'live': True}


@app.post(
        '/query',
        summary='Queries ChatGPT and gets response.'
)
async def prompt_gpt(params: GPTQueryParams):
    logging.info(f'prompt chatGPT request from user: {params.user_id}')
    response = call_gpt(params.query)
    
    if response:
        logging.info('Successfully queried chatGPT.')
    else:
        logging.info('Failed to query chatGPT.')

    return {'message': response}



if __name__ == '__main__':
    configs = read_configs(filename='./config.json')
    uvicorn.run('main:app', host=configs['host'], port=configs['port'], reload=True)