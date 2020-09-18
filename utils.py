import os
import json
import requests

# Config of rasa server
RASA_HOST = "127.0.0.1"
RASA_PORT = "5005"
BASE_URL = "http://{}:{}/webhooks/rest/webhook".format(RASA_HOST, RASA_PORT)

# Config of TTS module
TTS_INTERPRETER_PATH = "C:/Users/Doo/.conda/envs/pytorch"
TTS_MAIN_PATH = "D:/ProgramProjects/tts_module"
TTS_OUTPUT_PATH = TTS_MAIN_PATH + "/tacotron2_en_pretrained/output"
TTS_COMMAND_STRING = '{interpreter_path}/python.exe {main_path}/main.py -i "{input_text}" -o "{output_filepath}"'


def get_rasa_response(message: str, sender: str = "server"):
    """
    Send message to rasa server and get response
    :param message: String to be sent
    :param sender: String that identify sender
    :return: List of dicts
    """
    responses = requests.post(BASE_URL, data=json.dumps({"sender": sender, "message": message})).json()
    return responses


def text_to_voice(input_text: str, output_filename: str):
    """
    Convert sting to wav file
    :return: Int value, 0 means success, otherwise failure
    """
    cwd = os.getcwd()
    output_filepath = os.path.join(cwd, "data/" + output_filename)
    os.chdir(TTS_MAIN_PATH)
    return_val = os.system(TTS_COMMAND_STRING.format(interpreter_path=TTS_INTERPRETER_PATH,
                                                     main_path=TTS_MAIN_PATH,
                                                     input_text=input_text,
                                                     output_filepath=output_filepath))
    os.chdir(cwd)
    return return_val


if __name__ == '__main__':
    print(text_to_voice("hello world!", "hw.wav"))
