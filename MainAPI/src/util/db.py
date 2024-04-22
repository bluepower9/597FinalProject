import sqlalchemy
from sqlalchemy import create_engine
from util.util import read_configs
import logging
import chromadb
from util.modelparams import Document

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


class VectorDB():
    def __init__(self, threshold=1.5) -> None:
        self.configs = read_configs(filename='config.json')
        self.client = chromadb.PersistentClient(path = self.configs['database']['chromadb'])
        self.threshold = threshold


    def add_file(self, userid: int, docid: int, excerpts: list):
        collection = self.client.get_or_create_collection(f'user-{userid}')
        
        documents, ids = [], []
        for e in excerpts:
            documents.append(e['excerpt'])
            ids.append(str(e['excerpt_id'])) 

        collection.add(
            documents=documents,
            metadatas=[{'docid': docid} for i in range(len(documents))],
            ids=ids
        )

    
    def delete(self, userid:int, docid: int):
        try:
            collection = self.client.get_collection(f'user-{userid}')
            collection.delete(where={'docid': docid})

        except ValueError as e:
            logging.info('Could not find collection. error: ' + str(e))
            return False


    def query(self, s: str, userid: int):
        userid = f'user-{userid}'
        try:
            collection = self.client.get_collection(userid)

        except ValueError as e:
            logging.info('Could not find collection. error: ' + str(e))
            return []

        excerpts = collection.query(query_texts=s)
        result = []

        excerpts = zip(excerpts['ids'][0], excerpts['distances'][0], excerpts['documents'][0])

        for id, d, text in excerpts:
            if d <= self.threshold:
                result.append({'id': id, 'distance': d, 'text': text})

        return result

    


