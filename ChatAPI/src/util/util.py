import json
import logging


def read_configs(filename='config.json'):
    data = None
    try:
        with open(filename, 'r') as file:
            data = json.load(file)

    except Exception as e:
        logging.error(f'Error reading config file: {filename} - Exception: {str(e)}')
    
    return data