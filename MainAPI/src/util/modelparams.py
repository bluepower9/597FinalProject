from pydantic import BaseModel

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



