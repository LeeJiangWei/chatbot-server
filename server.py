# start command: uvicorn main:app --reload
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
import base64
import os

from utils import get_rasa_response, str_to_wav, wav_to_str, down_sample

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
    filename = "./data/{}.wav".format(name)
    wav_output_dir = os.path.join(os.getcwd(), "data")
    # Save the wav file from network
    with open(filename, "wb") as f:
        f.write(file.file.read())

    # Down sampling
    down_sample(filename, 16000)

    converted_str = wav_to_str(name)
    responses = get_rasa_response(converted_str, "server")

    for index, response in enumerate(responses):
        if "text" in response.keys():
            str_to_wav(response['text'], wav_output_dir)
            with open(os.path.join(wav_output_dir, "out.wav"), "rb") as f:
                wav_encoded = base64.b64encode(f.read())
                response["audio"] = wav_encoded

    return responses


@app.post("/message2audio")
def message_to_audio(message: Message):
    """
    Temp method, receive message, send audio response
    :param message:
    :return:
    """
    text = message.message
    filename = "response"
    if str_to_wav(text, filename):
        with open("./data/{}.wav".format(filename), "rb") as f:
            wav_encoded = base64.b64encode(f.read())
        return [{"attachment_base64": wav_encoded}]
    else:
        return [{"text": "语音转换失败"}]


def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    serve()
