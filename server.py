# start command: uvicorn server:app --reload
import base64
import io
import os
import socket
import threading
import zipfile

import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import FileResponse, StreamingResponse
from websockets.exceptions import WebSocketException

from utils import get_rasa_response, str_to_wav_file, wav_file_to_str, down_sample
from utils import wav_bin_to_str, str_to_wav_bin

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
    :return: responses in dict
    """
    # file name of wav file received from network
    filename = f"./data/{name}.wav"

    # output full path of speech synthesis
    wav_output_dir = os.path.join(os.getcwd(), "data")

    # Save the wav file from network
    with open(filename, "wb") as f:
        f.write(file.file.read())

    # Down sampling
    down_sample(filename, 16000)

    # convert wav to text, and get text response
    converted_str = wav_file_to_str(name)
    responses = get_rasa_response(converted_str)

    # for every returned response, if contains text, convert it into base64 encoded audio and add it
    for i, response in enumerate(responses):
        if "text" in response.keys():
            str_to_wav_file(response['text'], wav_output_dir)
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
            str_to_wav_file(response['text'], wav_output_dir)
            with open(os.path.join(wav_output_dir, "out.wav"), "rb") as f:
                wav_encoded = base64.b64encode(f.read())
                response["audio"] = wav_encoded

    return responses


lock = threading.Lock()


class STTReceiver(threading.Thread):
    def __init__(self, sock: socket.socket, websocket: WebSocket):
        threading.Thread.__init__(self)
        self.sock = sock
        self.websocket = websocket
        self.res = str()
        self.update_flag = False

    def run(self):
        print("Receiver started.")
        with open("./data/STT_result.txt", "w") as f:
            while True:
                try:
                    res = self.sock.recv(2048).decode("utf-8")

                    if not res.isspace():
                        lock.acquire()
                        self.res = res
                        self.update_flag = True
                        lock.release()

                        print("Recognize result: ", res)
                        f.write(res)

                except socket.timeout as e:
                    f.write(f"TimeoutException: {e}\n")
                    print(e)
                    break
        print("Receiver exit.")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    counter = 0
    data = bytes()
    try:
        while True:
            chunk = await websocket.receive_bytes()
            with open(f"./data/websocketAudio{counter}.wav", "wb") as f:
                f.write(chunk)
            counter += 1
            data += chunk
    except WebSocketDisconnect:
        print("Websocket disconnected.")
    except WebSocketException as e:
        print("Websocket Exception: ", e)
    finally:
        with open("./data/websocketAudio.wav", "wb") as f:
            f.write(data)

    # sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.connect((STT_HOST, STT_PORT))
    # sock.settimeout(10)
    # data = bytes()
    #
    # receiver_thread = STTReceiver(sock, websocket)
    # await websocket.accept()
    # try:
    #     receiver_thread.start()
    #     while receiver_thread.is_alive():
    #         chunk = await websocket.receive_bytes()
    #         data += chunk
    #         await websocket.send_text("Ack!")
    #
    #         sock.send(chunk)
    #         if not lock.locked():
    #             lock.acquire()
    #             if receiver_thread.update_flag:
    #                 res = receiver_thread.res
    #                 receiver_thread.update_flag = False
    #                 await websocket.send_text(res)
    #             lock.release()
    # except WebSocketDisconnect:
    #     print("Websocket disconnected.")
    # except WebSocketException as e:
    #     print("Websocket Exception: ", e)
    # finally:
    #     receiver_thread.join()
    #     sock.close()
    #     with open("./data/websocketAudio.wav", "wb") as f:
    #         f.write(data)
    #     print("Websocket endpoint exit.")


# Belows are for nano client


@app.post("/nano")
def response_wav_with_wav_bin(wav_data: bytes = File(...)):
    converted_str = wav_bin_to_str(wav_data)
    responses = get_rasa_response(converted_str, "nano")

    zip_container = io.BytesIO()
    zf = zipfile.ZipFile(zip_container, "w")

    for response in responses:
        if "text" in response.keys():
            text = response['text']

            wav = str_to_wav_bin(text)
            zf.writestr(text, wav)

    zf.close()
    zip_container.seek(0)

    return StreamingResponse(zip_container, media_type="application/x-zip-compressed")


app.mount("/", StaticFiles(directory="web/build"), name="static")


def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    serve()
