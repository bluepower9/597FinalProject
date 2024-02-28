import json
import logging
import bcrypt
import os
from fastapi import HTTPException, status


def read_configs(filename='config.json') -> dict:
    data = None
    try:
        with open(filename, 'r') as file:
            data = json.load(file)

    except Exception as e:
        logging.error(f'Error reading config file: {filename} - Exception: {str(e)}')
    
    return data


def validate_pw(pw:str, salt:int, hash:bytes):
    pass



async def download_upload_file(file, path):
    """
    downloads the file completely to the given path.
    """
    try:
        with open(path, "wb") as buffer:
            buffer.write(file.file.read())
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


