import nltk
from nltk.tokenize import sent_tokenize
from fastapi import HTTPException, status
import fitz
import re
from util.db import MySQLDatabase, VectorDB
from util.modelparams import *
from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, text
import logging


logging.basicConfig(level=logging.INFO)
nltk.download('punkt')
database = MySQLDatabase()
vectordb = VectorDB()

# Define a function to divide the input document into overlapping chunks
def divide_into_chunks(document, chunk_size=10, overlap=3):
    # Split the document into sentences using nltk tokenize
    sentences = sent_tokenize(document)
    # sentences = document.split('.')
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    # Divide the sentences into overlapping chunks
    chunks = []
    start_idx = 0
    while start_idx < len(sentences):
        end_idx = min(start_idx + chunk_size, len(sentences))
        chunk = " ".join(sentences[start_idx:end_idx])
        chunks.append(chunk)
        start_idx += chunk_size - overlap
    return chunks


def strip_excerpt_overlap(s, overlap=3, start=True, end=False):
    sentences = sent_tokenize(s)
    startindex = 0 if start else 2
    endindex = len(sentences)-3 if not end else len(sentences)

    return ' '.join(sentences[startindex: endindex])



async def download_upload_file(file, path):
    """
    downloads the file completely to the given path.
    """
    try:
        with open(path, "wb") as buffer:
            buffer.write(file.file.read())
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

def pdf_reader(filepath: str):
    extracted_text = []
    doc = fitz.open(filepath)
    for page in doc:
        text = [line for line in re.split('\n{2,100}',page.get_text()) if len(re.split(r'.', line))>5]
        extracted_text.extend(text)
    

    return ' '.join(extracted_text)


def create_new_doc(doc: Document) -> int:
    db = database.db

    try:
        with db.connect() as conn:
            query = text('INSERT INTO documents (title, user_id, descr) VALUES(:title, :user_id, :descr);')
            row = conn.execute(query, dict(title=doc.filename, user_id=doc.userid, descr=doc.description))
            conn.commit()
            doc.docid = row.lastrowid
            return row.lastrowid
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def save_excerpts_db(doc: Document) -> bool:
    '''
    Saves the excerpts to the database.

    Returns if it was successful.
    '''
    db = database.db
    if doc.docid is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='No doc id found for data.')
    try:
        with db.connect() as conn:
            for exc in doc.excerpts:
                query = text('INSERT INTO excerpts (excerpt, doc_id) VALUES(:excerpt, :doc_id);')
                conn.execute(query, dict(excerpt=exc, doc_id=doc.docid))
            
            conn.commit()
        
        logging.info('adding to vectordb...')
        vectordb.add_file(doc.userid, doc.docid, get_excerpts(doc.docid, doc.userid))


    except Exception as e:
        conn.close()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            
    return True


def get_user_files(userid: int) -> list:
    '''
    Fetches all the files for a given user.

    Returns [(docid, filename)]
    '''
    db = database.db
    if userid is None or type(userid) != int:
        return []
    
    try:
        with db.connect() as conn:
            query = text('SELECT doc_id, title, upload_ts, descr FROM documents WHERE user_id=:user_id;')
            data = conn.execute(query, dict(user_id=userid))
            data = data.mappings().fetchall()
            return data
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to fetch docs. error {e}')
    

def get_excerpts(doc_id: int, user_id: int) -> list:
    db = database.db
    if doc_id is None or type(doc_id) != int:
        return ''
    
    try:
        with db.connect() as conn:
            query = text('SELECT excerpt_id, excerpt FROM excerpts JOIN documents ON excerpts.doc_id=documents.doc_id WHERE excerpts.doc_id=:doc_id AND documents.user_id=:user_id ORDER BY excerpt_id ASC;')
            data = conn.execute(query, dict(user_id=user_id,doc_id=doc_id))
            data = data.mappings().fetchall()

            if len(data) == 0:
                return []
            
            return data
                     
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to fetch docs. error {e}')


def get_document(user_id: int, doc_id: int) -> str:

    if doc_id is None or type(doc_id) != int:
        return ''
    
    try:
        data = get_excerpts(doc_id, user_id)   
        if len(data) == 0:
            return ''
        
        result = ''
        for i, chunk in enumerate(data):
            result += strip_excerpt_overlap(chunk['excerpt'], end=(i==len(data)-1))
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to fetch docs. error {e}')


def delete_file(userid: int, doc_id: int) -> bool:
    '''
    Deletes the given document from the database.
    '''
    db = database.db

    try:
        with db.connect() as conn:
            query1 = text('DELETE FROM excerpts WHERE doc_id=:doc_id;')
            conn.execute(query1, dict(doc_id=doc_id))
            query2 = text('DELETE FROM documents WHERE doc_id=:doc_id;')
            data = conn.execute(query2, dict(doc_id=doc_id))
            conn.commit()

        vectordb.delete(userid, doc_id)

        return data.rowcount > 0

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Failed to delete document. error {e}')

    
    




