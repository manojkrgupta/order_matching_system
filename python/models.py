from pydantic import BaseModel

class mango_configuration(BaseModel):
        root_user: str
        root_pass: str
        url: str