import requests
from bs4 import BeautifulSoup


class Creature:
    def __init__(self, url: str, name: str):
        self.url = url
        self.name = name


class AonprdGrabber:
    __url = "https://2e.aonprd.com/"
    __get = "AspxAutoDetectCookieSupport=1"

    def __init__(self) -> None:
        self.__session = requests.Session()

    def __get_html(self, url: str):
        print(url)
        url = url.replace('\\', '/')
        if url.find('?') > 0:
            fin_url = f'{url}&{self.__get}'
        else:
            fin_url = f'{url}?{self.__get}'
        response = requests.get(fin_url)
        html = response.content
        if response.apparent_encoding is None:
            print('broken encoding')

        return html

    def get_creatures(self):
        html = self.__get_html(f'{self.__url}Creatures.aspx')
        soup = BeautifulSoup(html, 'html.parser')

        table = soup.find('table', class_="rgMasterTable")
        rows = table.find('tbody').find_all('tr')
        letters = {}

        for row in rows:
            link = row.find('td').find('a')
            url = link.get('href')
            name = self.__format_name(link.text)
            first_letter = name[0].upper()

            if first_letter not in letters.keys():
                letters[first_letter] = []

            letters[first_letter].append(Creature(url, name))

        return letters

    def __format_name(self, name: str):
        return name.lower().replace(' ', '_')

    def save_creature(self, path: str, creature: Creature):
        creature_url = f'{self.__url}{creature.url}'
        html = self.__get_html(creature_url)
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('img', class_='thumbnail')
        if img is not None:
            print(f'Image has found for {creature.name}')
            src = img.get('src')
            img_url = f'{self.__url}{src}'

            with open(f'{path}/{creature.name}.jpg', 'wb') as handler:
                response = requests.get(img_url, stream=True)

                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):
                    if not block:
                        break

                    handler.write(block)
        else:
            print(f'Image has not found for {creature.name}')
