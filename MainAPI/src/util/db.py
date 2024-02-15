import sqlalchemy
from sqlalchemy import create_engine
from util.util import read_configs
import logging

logging.basicConfig(level=logging.INFO)

class MySQLDatabase():
    def __init__(self):
        self.configs = read_configs(filename='config.json')
        self.__db = None
    

    def connect_db(self):
        uri = self.configs['database']['uri']
        try:
            logging.info('trying to connect to mySQL database...')
            self.__db = create_engine(uri, pool_pre_ping=True)
            logging.info('Successfully connected to mySQL database.')
            return self.__db

        except Exception as e:
            logging.error(f'Failed to connect to mySQL database. Error: {e}')
            return None

    @property
    def db(self):
        if not self.__db:
            return self.connect_db()

        return self.__db

