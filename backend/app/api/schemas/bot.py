from pydantic import BaseModel, Field


class BotCommandRequest(BaseModel):
    command: str = Field(min_length=1, max_length=2000)


class BotCommandResponse(BaseModel):
    reply: str
