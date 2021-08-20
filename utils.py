import os
import json
import requests
import socket

import librosa
import soundfile
import time

# Config of rasa server
RASA_HOST = "127.0.0.1"
RASA_PORT = 5005
BASE_URL = "http://{}:{}/webhooks/rest/webhook".format(RASA_HOST, RASA_PORT)

# Config of TTS module (speech synthesis)
TTS_HOST = "222.201.137.105"
TTS_PORT = 5051
TTS_URL = "http://{}:{}/synthesis".format(TTS_HOST, TTS_PORT)
TTS_URL_BIN = "http://{}:{}/binary".format(TTS_HOST, TTS_PORT)
TTS_DATA_PATH = "data"

# Config of ASR module (speech recognition)
ASR_HOST = "222.201.137.105"  # remote: 110.64.76.7
ASR_PORT = 5050


def get_rasa_response(message: str, sender: str = "server"):
    """
    Send message to rasa server and get response
    :param message: String to be sent
    :param sender: String that identify sender
    :return: List of dicts
    """
    responses = requests.post(BASE_URL, data=json.dumps({"sender": sender, "message": message})).json()
    return responses


def str_to_wav_file(input_str: str, output_dir: str = None):
    r = requests.post(TTS_URL, data=json.dumps({"text": input_str, "output_dir": output_dir}))
    print(r.json())


class asr_finite_state_machine:
    def __init__(self):
        self.curr_state = 'start'
        # trans 0: chinese or " " , 1: "/r" , 2: "/n"
        self.state_trans = {
            'start': ['recogn', 'start', 'start'],
            'recogn': ['recogn', 'start', 'end'],
            'end': ['end', 'end', 'end']
        }

    def set_start(self):
        self.curr_state = 'start'

    def get_state(self):
        return self.curr_state

    def trans(self, word):
        # trans: 0
        if '\u4e00' <= word <= '\u9fff' or word == " ":
            self.curr_state = self.state_trans[self.curr_state][0]
        # trans: 1
        elif word == '\r':
            self.curr_state = self.state_trans[self.curr_state][1]
        # trans : 2
        elif word == '\n':
            self.curr_state = self.state_trans[self.curr_state][2]


def wav_file_to_str(input_filename: str) -> str:
    """
    Convert wav file to string
    :param input_filename: file name of wav to be converted (without postfix)
    :return: converted string
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ASR_HOST, ASR_PORT))

    cwd = os.getcwd()
    input_file_path = os.path.join(cwd, TTS_DATA_PATH, input_filename + ".wav")

    buffer = ""
    with open(input_file_path, "rb") as f:
        wav = f.read()
        sock.send(wav)
        received_byte = sock.recv(2048)
        received_str = str(received_byte, encoding="utf-8")

        fsm = asr_finite_state_machine()
        words = list(received_str)
        while received_str != "":
            print(received_byte)
            print(received_str)
            print("--------------------------------------------")

            for word in words:
                fsm.trans(word)
                state = fsm.get_state()

                if state == 'start':
                    buffer = ''
                elif state == 'recogn':
                    buffer = buffer + word
                elif state == 'end':
                    buffer = buffer.replace(" ", "")
                    print("Final Recognized Result: ", buffer)
                    sock.close()
                    return buffer
            # buffer = received_str

            received_byte = sock.recv(2048)
            received_str = str(received_byte, encoding="utf-8")
            words = list(received_str)
    sock.close()
    buffer = buffer.replace(" ", "")
    print("Final Recognized Result: ", buffer)
    return buffer


def down_sample(filename: str, sample_rate: int) -> None:
    """
    Down sample a wav file to given sample rate
    :param filename: path to the wav file to be down sampled (with postfix)
    :param sample_rate: sample rate
    :return: None
    """
    y, sr = librosa.load(filename, sr=sample_rate)
    soundfile.write(filename, y, sr, format="wav")


def wav_bin_to_str(wav_data: bytes) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ASR_HOST, ASR_PORT))

    buffer = ""

    fsm = asr_finite_state_machine()

    sock.send(wav_data)
    received_byte = sock.recv(2048)
    received_str = str(received_byte, encoding="utf-8")
    words = list(received_str)
    while received_str != "":
        print(received_byte)
        print(received_str)
        print("-" * 80)

        for word in words:
            fsm.trans(word)
            state = fsm.get_state()

            if state == 'start':
                buffer = ''
            elif state == 'recogn':
                buffer = buffer + word
            elif state == 'end':
                buffer = buffer.replace(" ", "")
                print("Final Recognized Result: ", buffer)
                sock.close()
                return buffer
        # buffer = received_str

        received_byte = sock.recv(2048)
        received_str = str(received_byte, encoding="utf-8")
        words = list(received_str)

    sock.close()
    buffer = buffer.replace(" ", "")
    print("Final Recognized Result: ", buffer)
    return buffer


def str_to_wav_bin(input_str: str) -> bytes:
    r = requests.post(TTS_URL_BIN, json={"text": input_str})
    return r.content


def wav_file_to_str_debug(input_filename: str) -> str:
    """
    Convert wav file to string
    :param input_filename: file name of wav to be converted (without postfix)
    :return: converted string
    """

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ASR_HOST, ASR_PORT))

    cwd = os.getcwd()
    input_file_path = input_filename

    fsm = asr_finite_state_machine()

    buffer = ""

    start_time = time.time()
    with open(input_file_path, "rb") as f:
        wav = f.read()
        sock.send(wav)
        received_byte = sock.recv(2048)
        received_str = str(received_byte, encoding="utf-8")
        words = list(received_str)

        while received_str != "":
            print(received_byte)
            print(received_str)
            print("--------------------------------------------")

            for word in words:
                fsm.trans(word)
                state = fsm.get_state()

                if state == 'start':
                    buffer = ''
                elif state == 'recogn':
                    buffer = buffer + word
                elif state == 'end':
                    buffer = buffer.replace(" ", "")
                    print("Final Recognized Result: ", buffer)
                    print("recognition time:{}s".format(time.time() - start_time))
                    sock.close()
                    return buffer

            # buffer = received_str
            received_byte = sock.recv(2048)
            received_str = str(received_byte, encoding="utf-8")
            words = list(received_str)
    sock.close()
    buffer = buffer.replace(" ", "")
    print("Final Recognized Result: ", buffer)
    print("recognition time:{}s".format(time.time() - start_time))
    return buffer


if __name__ == '__main__':
    wav_file_to_str_debug(r'Weather.wav')
    # print(str_to_wav_file("hello world!", "hw.wav"))
