import json

import requests
from aonprd_grabber import AonprdGrabber

if __name__ == '__main__':
    grabber = AonprdGrabber()

    grabber.save_images()