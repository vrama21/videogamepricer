from curses import is_term_resized
import locale
import pprint
import ssl
from difflib import get_close_matches
from typing import List
from urllib.parse import urlencode

import aiohttp
import regex
from bs4 import BeautifulSoup
from bs4.element import Tag

pp = pprint.PrettyPrinter(indent=2)


class Game:
    def __init__(self, game):
        self.name = game["name"]
        self.system = game["system"]

        self.title = None
        self.box = game["box"] == "Yes"
        self.manual = game["manual"] == "Yes"

        self.loose_price = None
        self.complete_price = None
        self.new_price = None
        self.graded_price = None
        self.box_only_price = None
        self.manual_only_price = None

        self.estimated_value = 0

        self.url = None

    def __repr__(self) -> str:
        return str(self.__dict__)

    async def fetch_data(self, session: aiohttp.ClientSession):
        pricecharting_search_url = "https://www.pricecharting.com/search-products?"
        query_params = {
            "type": "prices",
            "q": self.name,
        }
        pricecharting_request_url = pricecharting_search_url + urlencode(query_params)

        async with session.get(
            pricecharting_request_url,
            ssl=ssl.SSLContext(),
        ) as search_response:
            print(f"Fetching results for {self.name} ...")

            search_response_html = await search_response.text()
            is_redirected = search_response.url.path != "/search-products"

            if is_redirected:
                self.parse_and_set_data(search_response_html)
            else:
                game_url = self.get_game_url(search_response_html)

                async with session.get(game_url, ssl=ssl.SSLContext()) as response:
                    html_response = await response.text()

                    self.parse_and_set_data(html_response)

        return self

    def get_game_url(self, html_response):
        soup = BeautifulSoup(html_response, "html.parser")
        games_table: Tag = soup.find("table", id="games_table").find("tbody")
        game_rows: List[Tag] = games_table.find_all("tr")

        search_results = []
        for row in game_rows:
            search_results.append(
                {
                    "system": row.find("td", class_="console").text.strip(),
                    "title": row.find("td", class_="title").find("a").text.strip(),
                    "url": row.find("a", href=True)["href"],
                }
            )

        results_for_console = [result for result in search_results if result["system"] == self.system]
        search_titles = [result["title"] for result in results_for_console]
        close_matches = get_close_matches(self.name, search_titles, n=1)

        if len(close_matches) > 0:
            best_match = next(
                (item for item in results_for_console if item["title"] == close_matches[0]),
                None,
            )

            self.url = best_match["url"]

        return self.url

    def get_price_by_id(self, price_data_table: Tag, id: str) -> float:
        if not price_data_table:
            return "N/A"

        element = price_data_table.find("td", id=id)

        div_price: str = element.find("span", class_="price js-price").text.strip()
        div_price = regex.sub(r"[,$\s]+", "", div_price)

        if div_price == "N/A":
            return "N/A"

        locale.setlocale(locale.LC_ALL, "")
        value = locale.atof(div_price)

        return value

    def parse_and_set_data(self, html_response):
        soup = BeautifulSoup(html_response, "html.parser")

        product_div = soup.find("h1", id="product_name")
        self.title = product_div.contents[0].text.strip()

        price_data_table: Tag = soup.find("table", id="price_data")
        self.loose_price = self.get_price_by_id(price_data_table, "used_price")
        self.complete_price = self.get_price_by_id(price_data_table, "complete_price")
        self.new_price = self.get_price_by_id(price_data_table, "new_price")
        self.graded_price = self.get_price_by_id(price_data_table, "graded_price")
        self.box_only_price = self.get_price_by_id(price_data_table, "box_only_price")
        self.manual_only_price = self.get_price_by_id(
            price_data_table,
            "manual_only_price",
        )

        if self.estimated_value > 0:
            return self.estimated_value

        if not self.loose_price == "N/A":
            self.estimated_value += self.loose_price

        if self.box:
            self.estimated_value += self.box_only_price

        if self.manual:
            self.estimated_value += self.manual_only_price
