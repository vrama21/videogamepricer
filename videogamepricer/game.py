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
        self.name: str = game["name"]
        self.system: str = game["system"]

        self.title: str | None = None
        self.box: bool = True if game.get("box", False) == 'Yes' else False
        self.manual: bool = True if game.get("manual", False) == 'Yes' else False

        self.loose_price = None
        self.complete_price = None
        self.new_price = None
        self.graded_price = None
        self.box_only_price = None
        self.manual_only_price = None

    def __dict__(self) -> dict:
        return {
            "name": self.name,
            "system": self.system,
            "loose_price": self.loose_price,
            "complete_price": self.complete_price,
            "new_price": self.new_price,
            "graded_price": self.graded_price,
            "box_only_price": self.box_only_price,
            "manual_only_price": self.manual_only_price,
            "estimated_value": self.get_estimated_value(),
        }

    def __repr__(self) -> str:
        return str(self.__dict__())

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

                if game_url:
                    async with session.get(game_url, ssl=ssl.SSLContext()) as response:
                        html_response = await response.text()

                        self.parse_and_set_data(html_response)

        return self.__dict__()

    def get_game_url(self, html_response: str) -> str:
        soup = BeautifulSoup(html_response, "html.parser")
        games_table: Tag = soup.find("table", id="games_table").find("tbody")
        game_rows: List[Tag] = games_table.find_all("tr")

        search_results = []
        for row in game_rows:
            search_result = {
                "system": row.find("td", class_="console").text.strip(),
                "title": row.find("td", class_="title").find("a").text.strip(),
                "url": row.find("a", href=True)["href"],
            }
            search_results.append(search_result)

        search_results_by_console = [result for result in search_results if result["system"] == self.system]
        search_results_titles = [result["title"] for result in search_results_by_console]

        close_title_matches = get_close_matches(self.name, search_results_titles, n=1)

        best_match_title = close_title_matches[0] if len(close_title_matches) > 0 else search_results_titles[0]

        best_match = next(
            (item for item in search_results_by_console if item["title"] == best_match_title),
            None,
        )

        return best_match["url"]

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

    def parse_and_set_data(self, html_response: str) -> None:
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

    def get_estimated_value(self) -> float:
        estimated_value = 0

        if not self.loose_price == "N/A":
            estimated_value += self.loose_price

        if self.box:
            estimated_value += self.box_only_price

        if self.manual:
            estimated_value += self.manual_only_price

        return estimated_value
