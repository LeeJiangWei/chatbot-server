import os
import json
import requests

# Config of rasa server
RASA_HOST = "127.0.0.1"
RASA_PORT = "5005"
BASE_URL = "http://{}:{}/webhooks/rest/webhook".format(RASA_HOST, RASA_PORT)

# Config of TTS module
TTS_DATA_PATH = "data/"
TTS_INTERPRETER_PATH = "C:/Users/Doo/.conda/envs/pytorch"
TTS_MAIN_PATH = "D:/ProgramProjects/tts_module"
TTS_OUTPUT_PATH = TTS_MAIN_PATH + "/tacotron2_en_pretrained/output"
TTS_COMMAND_STRING = '{interpreter_path}/python.exe {main_path}/main.py -i "{input_text}" -o "{output_file_path}"'

# Config of STT module
STT_DATA_PATH = "data/"
STT_MAIN_PATH = ""
STT_COMMAND = "run_custom.sh"
STT_COMMAND_STRING = '{command} "{input_dir_path}" "{output_file_path}"'


def get_rasa_response(message: str, sender: str = "server"):
    """
    Send message to rasa server and get response
    :param message: String to be sent
    :param sender: String that identify sender
    :return: List of dicts
    """
    responses = requests.post(BASE_URL, data=json.dumps({"sender": sender, "message": message})).json()
    return responses


def str_to_wav(input_str: str, output_filename: str):
    """
    Convert sting to wav file
    :param input_str: input str to be converted
    :param output_filename: output filename of wav file (without postfix)
    :return: Boolean value, True indicates success, False otherwise
    """
    cwd = os.getcwd()
    output_file_path = os.path.join(cwd, TTS_DATA_PATH, output_filename + ".wav")
    os.chdir(TTS_MAIN_PATH)
    return_val = os.system(TTS_COMMAND_STRING.format(interpreter_path=TTS_INTERPRETER_PATH,
                                                     main_path=TTS_MAIN_PATH,
                                                     input_text=input_str,
                                                     output_file_path=output_file_path))
    os.chdir(cwd)
    if not return_val:
        return True
    else:
        return False


def wav_to_str(input_filename: str, output_filename: str = "stt_output"):
    """
    Convert wav file to txt file
    :param input_filename: input filename of wav file to be converted (without postfix)
    :param output_filename: output filename of txt file (without postfix)
    :return: Str if success, False otherwise
    """
    cwd = os.getcwd()
    input_dir_path = os.path.join(cwd, STT_DATA_PATH)
    output_file_path = os.path.join(cwd, STT_DATA_PATH, output_filename)
    os.chdir(STT_MAIN_PATH)
    return_val = os.system(STT_COMMAND_STRING.format(command=STT_COMMAND,
                                                     input_dir_path=input_dir_path,
                                                     output_file_path=output_file_path))
    os.chdir(cwd)

    if not return_val:
        return False
    else:
        result_str = False
        with open(os.path.join(input_dir_path, output_filename + ".txt")) as f:
            for line in f:
                s = line.split(" ")
                if s[0] == input_filename:
                    result_str = "".join(s[1:]).replace("\n", "")
                    break
        return result_str


if __name__ == '__main__':
    print(str_to_wav("hello world!", "hw.wav"))
