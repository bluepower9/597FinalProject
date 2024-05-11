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




