# start command: uvicorn main:app --reload
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
import base64

from utils import get_rasa_response, text_to_voice

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000

app = FastAPI()


class Message(BaseModel):
    sender: str = None
    message: str = None


@app.post("/message")
def forward(message: Message):
    """
    Receive text message, simply forward it to rasa server
    :return: Response from rasa
    """
    return get_rasa_response(message.message, message.sender)


@app.post("/audio")
def upload_audio(name: str = Form(...), file: UploadFile = File(...)):
    """
    Receive blob(wav) file, store it to disk
    :param name: Name field in formdata, refers to file name
    :param file: File field in formdata, refers to the blob file
    :return: TODO: response with audio
    """
    with open("./data/{}.wav".format(name), "wb") as f:
        f.write(file.file.read())

    return {"text": "成功接收语音，回复功能尚未完成"}


@app.post("/message2audio")
def message_to_audio(message: Message):
    """
    Temp method, receive message, send audio response
    :param message:
    :return:
    """
    text = message.message
    filename = "response.wav"
    if not text_to_voice(text, filename):
        with open("./data/" + filename, "rb") as f:
            wav_encoded = base64.b64encode(f.read())
        return [{"attachment_base64": wav_encoded}]
    else:
        return [{"text": "语音转换失败"}]


def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    serve()
