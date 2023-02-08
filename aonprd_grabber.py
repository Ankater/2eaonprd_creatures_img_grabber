import json
import logging
import logging.config
import os
import socket
import time

import requests
from bs4 import BeautifulSoup

logging.config.fileConfig('logging.conf')


# TODO add normal logging
class AonprdGrabber:
    logger: logging.Logger
    __url = "https://2e.aonprd.com/"
    __get = "AspxAutoDetectCookieSupport=1"
    __path_base = 'creatures'

    MAX_REQUEST_ATTEMPTS = 5
    TIMEOUT = 5
    TIMEOUT_STREAM = 20
    SLEEP_TIME = 5

    def __init__(self) -> None:
        self.logger = logging.getLogger('2eaonprd')
        if not os.path.exists(self.__path_base):
            try:
                os.mkdir(self.__path_base)
            except FileExistsError as exc:
                self.logger.error(exc.strerror)
        self.__session = requests.Session()

    def __get_html(self, url: str):
        self.logger.info(url)
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
            self.logger.error('broken encoding')

        return html

    def save_creature(self, url: str):
        html = self.__get_creature_page(url)
        if html is None:
            self.logger.info(f'Can`t find creatue {url}')
            return True

        soup = BeautifulSoup(html, 'html.parser')
        main = soup.find('div', id='main')
        title = main.find('h1', {'class': 'title'})
        if title is None:
            self.logger.info(f'Can`t find name for creatue {url}')
            return None

        creature_name = title.text
        img = soup.find('img', {'class': 'thumbnail'})
        if img is not None:
            self.logger.info(f'Image has found for {creature_name}')
            dir_name = creature_name[0].upper()
            path = self.__make_path(dir_name)
            file_path = f'{path}/{creature_name}.jpg'
            if os.path.exists(file_path):
                self.logger.info('img already exists')
                return True

            src = img.get('src')
            img_url = f'{self.__url}{src}'

            self.logger.info('start downloading img')
            with open(f'{path}/{creature_name}.jpg', 'wb') as handler:
                # response = requests.get(img_url, stream=True)
                response = self.__request_get(img_url, True)

                if not response.ok:
                    self.logger.debug(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handler.write(block)
            self.logger.info('stop downloading img')
        else:
            self.logger.info(f'Image has not found for {creature_name}')

        return True

    def __get_creature_page(self, url: str):
        creature_url = f'{self.__url}{url}'
        html = self.__get_html(creature_url)

        return html

    def __make_path(self, dir_name) -> str:
        path = f'{self.__path_base}/{dir_name}'
        if not os.path.exists(path):
            try:
                os.mkdir(path)
            except FileExistsError as exc:
                self.logger.error(exc)

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
                self.logger.error(e.strerror)
                request_attempts += 1
                self.logger.debug(request_attempts)
                time.sleep(self.SLEEP_TIME)

            except socket.timeout as e:
                self.logger.error(e.strerror)
                request_attempts += 1
                self.logger.debug(request_attempts)
                time.sleep(self.SLEEP_TIME)

            except requests.exceptions.ConnectionError as e:
                self.logger.error(e.strerror)
                request_attempts += 1
                self.logger.debug(request_attempts)
                time.sleep(self.SLEEP_TIME)

        return response

    def save_images(self):
        creatures = self.get_creatures_list()
        for creature in creatures:
            source = creature.get('_source')
            if source is None:
                continue
            url = source.get('url')
            if type(url) is not str:
                continue

            self.save_creature(url)

    def get_creatures_list(self):
        url = 'https://elasticsearch.aonprd.com/aon/_search?track_total_hits=true'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0',
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json',
            'Origin': 'https://2e.aonprd.com',
            'Connection': 'keep-alive',
            'Referer': 'https://2e.aonprd.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site'
        }
        data = '{"query":{"function_score":{"query":{"bool":{"filter":[{"query_string":{"query":"category:creature","default_operator":"AND","fields":["name","text^0.1","trait_raw","type"]}}]}},"boost_mode":"multiply","functions":[{"filter":{"terms":{"type":["Ancestry","Class"]}},"weight":1.1},{"filter":{"terms":{"type":["Trait"]}},"weight":1.05}]}},"size":10000,"sort":[{"name.keyword":{"order":"asc"}},"_doc"],"_source":{"excludes":["text"]}}'

        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200:
            return []

        data = json.loads(response.text)
        hits = data.get('hits', [])
        if type(hits) is not dict:
            return []
        return hits.get('hits', [])
