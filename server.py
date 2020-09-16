# start command: uvicorn main:app --reload
import uvicorn
import requests
import json

from typing import Optional
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel

HOST = "127.0.0.1"
PORT = 8000

RASA_HOST = "127.0.0.1"
RASA_PORT = "5005"
BASE_URL = "http://{}:{}/webhooks/rest/webhook".format(RASA_HOST, RASA_PORT)

app = FastAPI()


class Message(BaseModel):
    sender: str = None
    message: str = None


def get_rasa_response(message: str, sender: str = "server"):
    """
    Send message to rasa server and get response
    :param message: String to be sent
    :param sender: String that identify sender
    :return: List of strings
    """
    responses = requests.post(BASE_URL, data=json.dumps({"sender": sender, "message": message})).json()
    return responses


@app.post("/message")
def forward(message: Message):
    """
    For text message, simply forward it to rasa server
    :return: Response from rasa
    """
    return get_rasa_response(message.message, message.sender)


@app.post("/audio")
def upload_audio(file: UploadFile = File(...)):
    return {"text": "成功接收语音，回复功能尚未完成"}


def serve():
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == '__main__':
    serve()
