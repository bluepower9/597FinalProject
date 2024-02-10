from pydantic import BaseModel

class GPTQueryParams(BaseModel):
    query: str

    # to be implemented later
    excerpt: str
    user_id: int
    session_id: str



