from fastapi import APIRouter, Depends, Form, UploadFile, File
from typing import Annotated
from util.auth import get_current_user
import logging
from util.util import download_upload_file


router = APIRouter(
    dependencies=[Depends(get_current_user)],
    prefix='/documents',
    tags=['document processing'],
    responses={404: {'description': 'Not found'}}
)


@router.post('/upload')
async def upload_document(
    file: UploadFile = File()
):
    filename = file.filename
    dl_path = f'./temp/{filename}'
    logging.info(f'received file: {filename}')

    await download_upload_file(file, dl_path)


    
    

