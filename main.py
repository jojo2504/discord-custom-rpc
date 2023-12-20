import requests
import json
import time
import pywinauto.application
import _ctypes
from threading import Thread
from pypresence import Presence
from datetime import timedelta
from win32gui import GetForegroundWindow
from win32process import GetWindowThreadProcessId
from config import *

class Clock():
    @staticmethod
    def format_seconds(seconds):
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        if hours == 0:
            return '{:02}:{:02}'.format(int(minutes), int(seconds))
        else:
            return '{:02}:{:02}:{:02}'.format(int(hours), int(minutes), int(seconds))

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
        return str(self.request.status_code)

class Application():
    def __init__(self, ID) -> None:
        self.ID = ID
        self.RPC = Presence(self.ID)
        self.infos = API()
        self.infos.start()

        self.active_tab = ActiveTab()
        self.active_tab.start()

        self.seconds = 0

    def connect(self):
        self.RPC.connect()

    def update(self):
        try:
            self.seconds += 1
            self.RPC.update(
                details = "{} | Problems solved: {}".format(self.active_tab.active_tab, self.infos.content["totalSolved"]),
                state = "{} elapsed".format(Clock.format_seconds(self.seconds)),
                large_image = "leetcode_logo",
                large_text = "LeetCode",
                buttons = [
                    {"label": button_1_text, "url": button_1_url}, 
                    {"label": button_2_text, "url": button_2_url}
                ],
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
