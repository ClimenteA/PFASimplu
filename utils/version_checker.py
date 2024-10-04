import requests


verurl = "https://raw.githubusercontent.com/ClimenteA/PFASimplu/refs/heads/main/static/versiune.txt"


def new_version_available():
    try:
        with open("versiune.txt", "r") as f:
            vcurrent = f.read()

        response = requests.get(verurl)
        return vcurrent != response.text

    except:
        return False
    