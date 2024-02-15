import json
import logging
import bcrypt



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




