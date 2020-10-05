# start command: uvicorn main:app --reload
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import FileResponse
import base64
import os

from utils import get_rasa_response, str_to_wav, wav_to_str, down_sample

SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

app = FastAPI()


class Message(BaseModel):
    sender: str = None
    message: str = None


@app.get("/")
def index():
    return FileResponse("web/build/index.html")


@app.post("/message")
def response_message_with_message(message: Message):
    """
    Receive text message, simply forward it to rasa server
    :return: Response from rasa
    """
    return get_rasa_response(message.message, message.sender)


@app.post("/audio")
def response_audio_with_audio(name: str = Form(...), file: UploadFile = File(...)):
    """
    Receive blob(wav) file, store it to disk
    :param name: Name field in formdata, refers to file name
    :param file: File field in formdata, refers to the blob file
    :return: TODO: response with audio
    """
    # file name of wav file received from network
    filename = "./data/{}.wav".format(name)

    # output full path of speech synthesis
    wav_output_dir = os.path.join(os.getcwd(), "data")

    # Save the wav file from network
    with open(filename, "wb") as f:
        f.write(file.file.read())

    # Down sampling
    down_sample(filename, 16000)

    # convert wav to text, and get text response
    converted_str = wav_to_str(name)
    responses = get_rasa_response(converted_str)

    # for every returned response, if contains text, convert it into base64 encoded audio and add it
    for i, response in enumerate(responses):
        if "text" in response.keys():
            str_to_wav(response['text'], wav_output_dir)
            with open(os.path.join(wav_output_dir, "out.wav"), "rb") as f:
                wav_encoded = base64.b64encode(f.read())
                response["audio"] = wav_encoded

    return responses


@app.post("/message2audio")
def response_message_with_audio(message: Message):
    """
    Temp method, receive message, send audio response
    :param message:
    :return:
    """
    wav_output_dir = os.path.join(os.getcwd(), "data")

    text = message.message

    responses = get_rasa_response(text)
    for index, response in enumerate(responses):
        if "text" in response.keys():
            str_to_wav(response['text'], wav_output_dir)
            with open(os.path.join(wav_output_dir, "out.wav"), "rb") as f:
                wav_encoded = base64.b64encode(f.read())
                response["audio"] = wav_encoded

    return responses


app.mount("/", StaticFiles(directory="web/build"), name="static")


def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    serve()
