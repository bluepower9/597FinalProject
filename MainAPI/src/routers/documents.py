from fastapi import APIRouter, Depends, Form, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from util.auth import get_current_user, oauth2_scheme
import logging
from util.docprocessing import *
import os
import time
from util.modelparams import *



router = APIRouter(
    dependencies=[Depends(oauth2_scheme)],
    prefix='/documents',
    tags=['document processing'],
    responses={404: {'description': 'Not found'}}
)


@router.post('/upload', summary='Upload a PDF document to the server.')
async def upload_document(
    userinfo: Annotated[UserInfo, Depends(get_current_user)],
    file: UploadFile = File(),
    title: str = Form(default=None),
    description: str = Form()
):
    if title is None or title.strip() == '':
        filename = file.filename
    else:
        filename = title

    dl_path = f'./temp/{filename}'
    logging.info(f'received file: {filename}')

    await download_upload_file(file, dl_path)
    logging.info('Finished downloading file to temp.')

    logging.info('Extracting data from file...')
    excerpts = pdf_reader(dl_path)

    logging.info('dividing data in chunks...')
    chunks = divide_into_chunks(excerpts)

    os.remove(dl_path)

    description = "" if not description else description.strip()

    logging.info('saving to db...')
    doc = Document(userid=userinfo.userid, filename=filename, excerpts=chunks, description=description)
    docid = create_new_doc(doc)
    logging.info(f'created new doc: {docid}')
    save_excerpts_db(doc)
    logging.info(f'Successfully saved excerpts for doc: {docid}')

    return {'doc_id': docid, 'excerpts': chunks}


@router.post('/delete', summary='Remove a document from the account.')
async def delete_document(
    userinfo: Annotated[UserInfo, Depends(get_current_user)],
    doc_id: int = Form()
):
    docs = get_user_files(userinfo.userid)
    all_doc_ids = [d['doc_id'] for d in docs]
    if doc_id not in all_doc_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Document not found for user.')
    
    success = delete_file(userinfo.userid, doc_id)

    return {'deleted': success, 'doc_id': doc_id}


@router.post('/list-all', summary='Lists all documents for the user.')
async def fetch_all_documents_for_user(
    userinfo: Annotated[UserInfo, Depends(get_current_user)]
):
    docs = get_user_files(userinfo.userid)
    return {'documents': docs}


@router.post('/file', summary='get extracted text for a given document for the user.')
async def fetch_file_text(
    userinfo: Annotated[UserInfo, Depends(get_current_user)],
    doc_id: int = Form()
):
    return {'text': get_document(userinfo.userid, doc_id)}








    
    

