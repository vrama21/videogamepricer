import asyncio
from typing import NamedTuple, List
from bs4 import BeautifulSoup
from bs4.element import Tag
import aiohttp
import ssl
import regex
import locale

locale.setlocale(locale.LC_ALL, '')


class GameProps(dict):
    name: str
    system: str


class Game:
    def __init__(self, game: GameProps):
        self.name = game['name']
        self.system = game['system']

        self.loose_price = None
        self.complete_price = None
        self.new_price = None
        self.graded_price = None
        self.box_only_price = None
        self.manual_only_price = None

        self.url = self.get_request_url()

    def __repr__(self) -> str:
        return str(self.__dict__())

    def get_request_url(self) -> List[str]:
        game_system = '-'.join(self.system.lower().split())
        game_name = '-'.join(self.name.lower().split())

        request_url = f"https://www.pricecharting.com/game/{game_system}/{game_name}"

        return request_url

    def get_price_by_id(self, price_data_table: Tag, id: str) -> float:
        if not price_data_table:
            return 'N/A'

        element = price_data_table.find('td', id=id)

        div_price: str = element.find('span', class_='price js-price').text.strip()
        div_price = regex.sub(r'[,$\s]+', '', div_price)

        if div_price == 'N/A':
            return 'N/A'

        value = locale.atof(div_price)
        return value

    def get_data(self, html_response):
        soup = BeautifulSoup(html_response, 'html.parser')
        price_data_table: Tag = soup.find('table', id='price_data')

        self.loose_price = self.get_price_by_id(price_data_table, 'used_price')
        self.complete_price = self.get_price_by_id(price_data_table, 'complete_price')
        self.new_price = self.get_price_by_id(price_data_table, 'new_price')
        self.graded_price = self.get_price_by_id(price_data_table, 'graded_price')
        self.box_only_price = self.get_price_by_id(price_data_table, 'box_only_price')
        self.manual_only_price = self.get_price_by_id(price_data_table, 'manual_only_price')