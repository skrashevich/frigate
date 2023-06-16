import faulthandler
import os
import threading

import grpc
from frigate.version import VERSION


from flask import cli

from frigate.app import FrigateApp

faulthandler.enable()

threading.current_thread().name = "frigate"

cli.show_server_banner = lambda *x: None

if __name__ == "__main__":
    frigate_app = FrigateApp()

    frigate_app.start()
