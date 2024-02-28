from pydantic import BaseModel
from typing import Annotated
from fastapi import Form, UploadFile

class Token(BaseModel):
    access_token: str
    token_type: str

class RegisterUser(BaseModel):
    username: str
    email: str
    password: str


class LoginUser(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    userid: int
    username: str
    email: str
    password: bytes
    salt: bytes


class Token(BaseModel):
    access_token:str
    token_type: str




