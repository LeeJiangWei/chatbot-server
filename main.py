import requests
import json

RASA_HOST = "127.0.0.1"
RASA_PORT = "5002"
BASE_URL = "http://{}:{}/api".format(RASA_HOST, RASA_PORT)

RASA_USERNAME = "me"
RASA_PASSWORD = "password"

ACCESS_TOKEN = ""


def auth():
    """
    login to rasa x server
    :return: boolean value indicating success or not
    """
    r = requests.post(BASE_URL + "/auth",
                      data=json.dumps({"username": RASA_USERNAME, "password": RASA_PASSWORD})).json()
    if 'access_token' in r.keys():
        global ACCESS_TOKEN
        ACCESS_TOKEN = r['access_token']
        return True
    else:
        return False


def initialize():
    auth()


if __name__ == '__main__':
    initialize()
