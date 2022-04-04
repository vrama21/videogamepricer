import asyncio
import pprint
import ssl
import sys
from pathlib import Path
from typing import List

import aiohttp
from pandas import DataFrame, read_csv, to_numeric

from videogamepricer.game import Game

pp = pprint.PrettyPrinter(indent=4)


async def fetch(game: Game, session: aiohttp.ClientSession):
    async with session.get(game.url, ssl=ssl.SSLContext()) as response:
        print(f'Fetching {game.url} ...')

        html_response = await response.text()

        game.get_data(html_response)

        return game


async def fetch_all(games: List[Game], loop: asyncio.AbstractEventLoop):
    async with aiohttp.ClientSession(loop=loop) as session:
        fetches = [fetch(game, session) for game in games]

        game_list = await asyncio.gather(*fetches, return_exceptions=True)

        return game_list


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        print('Missing argument: CSV file path')
        return

    csv_file_name = args[0]

    csv_path = Path(__file__).parent.parent.resolve() / 'data' / csv_file_name
    game_records = read_csv(csv_path).to_dict(orient='records')

    loop = asyncio.get_event_loop()

    games = [Game(game) for game in game_records]
    games = loop.run_until_complete(fetch_all(games, loop))
    game_data = [game.__dict__ for game in games]

    df = DataFrame.from_records(data=game_data)
    # df.loc["Total"] = to_numeric(df.sum(numeric_only=True, axis=0))

    csv_path = 'data/videogamepricer.csv'
    print(f'Saving to {csv_path} ...')
    df.to_csv(csv_path, index=False)
