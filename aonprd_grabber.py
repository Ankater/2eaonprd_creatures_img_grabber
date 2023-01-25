import os
import socket
import time

import requests
from bs4 import BeautifulSoup


# TODO add normal logging
class AonprdGrabber:
    __url = "https://2e.aonprd.com/"
    __get = "AspxAutoDetectCookieSupport=1"
    __uri_monster = "Monsters.aspx"
    __uri_npc = "NPCs.aspx"
    __curr_id = 1
    __path_base = 'creatures'
    __fail_counter = 0

    MAX_FAILS = 500
    MAX_REQUEST_ATTEMPTS = 10
    TIMEOUT = 5
    TIMEOUT_STREAM = 20
    SLEEP_TIME = 5

    def __init__(self) -> None:
        if not os.path.exists(self.__path_base):
            try:
                os.mkdir(self.__path_base)
            except FileExistsError as exc:
                print(exc)
        self.__session = requests.Session()

    def __get_html(self, url: str):
        # TODO add time limit for requests
        print(url)
        url = url.replace('\\', '/')
        if url.find('?') > 0:
            fin_url = f'{url}&{self.__get}'
        else:
            fin_url = f'{url}?{self.__get}'

        response = self.__request_get(fin_url)
        if response is None or response.status_code != 200:
            return None

        html = response.content
        if response.apparent_encoding is None:
            print('broken encoding')

        return html

    def save_creature(self):
        html = self.__get_creature_page()
        self.__curr_id += 1
        if html is None:
            print(f'Can`t find creatue №{self.__curr_id - 1}')
            self.__fail_counter += 1
            if self.__fail_counter >= self.MAX_FAILS:
                return None
            else:
                return True

        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('div', id='main')
        title = main.find('h1', {'class': 'title'})
        if title is None:
            print(f'Can`t find name for creatue №{self.__curr_id - 1}')
            return None

        creature_name = title.text
        img = soup.find('img', {'class': 'thumbnail'})
        if img is not None:
            print(f'Image has found for {creature_name}')
            dir_name = creature_name[0].upper()
            path = self.__make_path(dir_name)

            src = img.get('src')
            img_url = f'{self.__url}{src}'

            print('start downloading img')
            with open(f'{path}/{creature_name}.jpg', 'wb') as handler:
                # response = requests.get(img_url, stream=True)
                response = self.__request_get(img_url, True)

                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handler.write(block)
            print('stop downloading img')
        else:
            print(f'Image has not found for {creature_name}')

        return True

    def __get_creature_page(self):
        id_str = f'?ID={self.__curr_id}'
        creature_url = f'{self.__url}{self.__uri_monster}{id_str}'
        html = self.__get_html(creature_url)
        if html is None:
            npc_url = f'{self.__url}{self.__uri_npc}{id_str}'
            html = self.__get_html(npc_url)

        return html

    def __make_path(self, dir_name) -> str:
        path = f'{self.__path_base}/{dir_name}'
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except FileExistsError as exc:
                print(exc)

        return path

    def __request_get(self, fin_url, stream=False):
        request_attempts = 0
        response = None
        while request_attempts < self.MAX_REQUEST_ATTEMPTS:
            try:
                if stream:
                    response = requests.get(fin_url, timeout=self.TIMEOUT_STREAM, stream=True)
                else:
                    response = requests.get(fin_url, timeout=self.TIMEOUT)
                break
            except requests.Timeout as e:
                print(e.strerror)
                request_attempts += 1
                print(request_attempts)
                time.sleep(self.SLEEP_TIME)

            except socket.timeout as e:
                print(e.strerror)
                request_attempts += 1
                print(request_attempts)
                time.sleep(self.SLEEP_TIME)

            except ConnectionError as e:
                print(e.strerror)
                request_attempts += 1
                print(request_attempts)
                time.sleep(self.SLEEP_TIME)

        return response
