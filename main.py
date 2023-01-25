import os

from aonprd_grabber import AonprdGrabber

if __name__ == '__main__':
    grabber = AonprdGrabber()

    while True:
        if grabber.save_creature() is None:
            break