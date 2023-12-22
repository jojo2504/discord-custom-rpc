import requests
import json
import time
import pywinauto.application
import _ctypes
import os
from threading import Thread
from pypresence import Presence
from datetime import timedelta
from win32gui import GetForegroundWindow
from win32process import GetWindowThreadProcessId
from config import *

class Command(Thread):
    def __init__(self, application):
        Thread.__init__(self, daemon=True)
        self.application = application
    
    def run(self):
        while True:
            self.user_input = input()
            if self.user_input == "print(api.infos)":
                print(self.application.infos)
                os.system('cls' if os.name == 'nt' else 'clear')

class ActiveTab(Thread):
    def __init__(self):
        Thread.__init__(self, daemon=True)
        self.active_tab = "Idling"

    def run(self):
        self.get_url()

    def get_url(self):
        while True:
            time.sleep(3)
            try:
                window = GetForegroundWindow()
                tid, pid = GetWindowThreadProcessId(window)

                app = pywinauto.application.Application(backend="uia").connect(process=pid)
                dlg = app.top_window()
                url = dlg.child_window(title="Address and search bar", control_type="Edit").get_value()

                if "leetcode.com" in url:
                    url = url.split('/')
                    if url[2] == '':
                        self.active_tab = "In The Menu"
                    else:
                        self.active_tab = url[2].replace('-', ' ').title()
                else:
                    self.active_tab = "Idling"
                    
            except (pywinauto.findwindows.ElementNotFoundError, RuntimeError, IndexError, _ctypes.COMError) as e:
                print(e.args)
                self.active_tab = "Idling"  

class API(Thread):
    def __init__(self) -> None:
        Thread.__init__(self, daemon=True)
        self.request = requests.get("https://leetcode-stats-api.herokuapp.com/{}".format(USERNAME))
        self.content = self.convertJson(self.request.content)
    
    def run(self):
        self.fetch_data()

    def convertJson(self, content):
        json_string = content.decode('utf-8')
        return json.loads(json_string)
    
    def fetch_data(self):
        while True:
            self.request = requests.get("https://leetcode-stats-api.herokuapp.com/{}".format(USERNAME))
            self.content = self.convertJson(self.request.content)
            time.sleep(10)

    def __str__(self):
        return str(self.content)

class Application():
    def __init__(self, ID) -> None:
        self.ID = ID
        self.RPC = Presence(self.ID)
        self.infos = API()
        self.infos.start()

        self.active_tab = ActiveTab()
        self.active_tab.start()

        self.start_time = time.time()

        self.command = Command(self)
        self.command.start()

    def connect(self):
        self.RPC.connect()

    def update(self):
        try:
            self.RPC.update(
                details = "{} | Problems solved: {}".format(self.active_tab.active_tab, self.infos.content["totalSolved"]),
                state = "Rank: {}".format(self.infos.content["ranking"]),
                large_image = "leetcode_logo",
                large_text = "LeetCode",
                buttons = [
                    {"label": button_1_text, "url": button_1_url}, 
                    {"label": button_2_text, "url": button_2_url}
                ],
                start=self.start_time,
            )
        except KeyError as e:
            print(e.args)

def main():
    application = Application(application_ID)
    application.connect()
    
    while True:
        time.sleep(1)
        application.update()

if __name__ == "__main__":
    main()
