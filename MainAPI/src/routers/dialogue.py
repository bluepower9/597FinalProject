from fastapi import APIRouter, FastAPI, HTTPException, Form, Depends
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import logging
from util import *
from util.modelparams import *
from util.gpt import *
from util.auth import *
from util.db import VectorDB

vectordb = VectorDB()

logging.basicConfig(level=logging.INFO)


router = APIRouter(
    dependencies=[Depends(oauth2_scheme)],
    prefix='/chat',
    tags=['dialogue'],
    responses={404: {'description': 'Not found'}}
)


@router.post(
        '/query',
        summary='Queries ChatGPT and gets response.'
)
async def prompt_gpt(
    userinfo: Annotated[UserInfo, Depends(get_current_user)],
    query: str = Form()
):
    excerpts = vectordb.query(query, userinfo.userid)
    if len(excerpts) == 0:
        return {'message': "I'm sorry, I could not find any information relating to your query."}

    logging.info(f'prompt chatGPT request from user: {userinfo.userid}')
    response = call_gpt(query, [e['text'] for e in excerpts])
    
    if response:
        logging.info('Successfully queried chatGPT.')
    else:
        logging.info('Failed to query chatGPT.')

    return {'message': response, 'excerpts': excerpts}

