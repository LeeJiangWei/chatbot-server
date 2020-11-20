# start command: uvicorn server:app --reload
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect
from websockets.exceptions import WebSocketException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.responses import FileResponse
import base64
import os
import socket
import threading

from utils import get_rasa_response, str_to_wav, wav_to_str, down_sample
from utils import STT_HOST, STT_PORT

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
lock= threading.Lock()
class STTReciever(threading.Thread):
    def __init__(self,sock:socket.socket,websocket:WebSocket):
        threading.Thread.__init__(self)
        self.sock=sock
        self.websocket=websocket
        self.res=str()
        # self.lock=lock
        self.update_flag=False
    def run(self):
        count=0
        print("reciever_running...")
        f=open("./data/TTS_result.txt","a")
        while(1):
            try:
                # f.write("loop:{}\n".format(count))

                count+=1

                res=self.sock.recv(2048).decode("utf-8")
                lock.acquire()
                print("lock acquired by reciever")
                self.res=res
                self.update_flag=True
                lock.release()
                print("lock released by reciever")

                # self.res=res
                # self.update_flag=True
                if(res):
                    print(res)
                    # self.websocket.send_text("res")
                    f.write(res)
                    if(res.split()[0]!="0.00"):
                        break
                    # f.close()
                else: break
            except socket.timeout as e:
                f.write("TimeoutException: {}\n".format(e))
                continue
        f.close()
        # except:
        #     pass# break


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((STT_HOST, STT_PORT))
    # sock.setblocking(False)
    sock.settimeout(10)
    data = bytes()
    # lock=threading.Lock()
    reciever_thread=STTReciever(sock,websocket)
    await websocket.accept()
    try:
        reciever_thread.start()
        while True:
            chunk = await websocket.receive_bytes()
            data += chunk
            await websocket.send_text("Ack!")
            sock.send(chunk)
            if(not lock.locked()):
                lock.acquire()
                if(reciever_thread.update_flag==True):
                    res=reciever_thread.res
                    reciever_thread.update_flag=False
                    lock.release()
                    print("send ws")
                    await websocket.send_text(res)
                else: lock.release()
    except WebSocketDisconnect:
        print("Websocket disconnected")
    except WebSocketException as e:
        print("Websocket Exception: ", e)
    finally:
        reciever_thread.join()
        sock.close()
        with open("./data/websocketAudio.wav", "wb") as f:
            f.write(data)

app.mount("/", StaticFiles(directory="web/build"), name="static")


def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)


if __name__ == '__main__':
    serve()
