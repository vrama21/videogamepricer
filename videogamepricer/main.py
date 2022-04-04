import asyncio
import ssl
from pathlib import Path

import aiohttp
from pandas import DataFrame, read_csv, to_numeric
from typing import List
from videogamepricer.game import Game, GameProps


# csv_path = Path(__file__).parent.resolve() / 'data' / 'sega_genesis.csv'
# games = read_csv(csv_path).iloc[:, 0].tolist()

async def fetch(game: Game, session: aiohttp.ClientSession):
    async with session.get(game.url, ssl=ssl.SSLContext()) as response:
        print(f'Fetching {game.url} ...')

        html_response = await response.text()

        game.get_data(html_response)

        return game.__dict__


async def fetch_all(games: List[Game], loop: asyncio.AbstractEventLoop):
    async with aiohttp.ClientSession(loop=loop) as session:
        fetches = [fetch(game, session) for game in games]

        game_list = await asyncio.gather(*fetches, return_exceptions=True)

        return game_list


def main():
    game_list: List[GameProps] = [
        {'name': 'Pokemon Red', 'system': 'Gameboy'},
        {'name': 'Pokemon Blue', 'system': 'Gameboy'},
        {'name': 'Pokemon Yellow', 'system': 'Gameboy'},
        {'name': 'Pokemon Gold', 'system': 'Gameboy Color'},
        {'name': 'Pokemon Silver', 'system': 'Gameboy Color'},
        {'name': 'Pokemon Crystal', 'system': 'Gameboy Color'},
        {'name': 'Pokemon Ruby', 'system': 'Gameboy Advance'},
        {'name': 'Pokemon Sapphire', 'system': 'Gameboy Advance'},
        {'name': 'Pokemon Emerald', 'system': 'Gameboy Advance'},
        {'name': 'Pokemon FireRed', 'system': 'Gameboy Advance'},
        {'name': 'Pokemon LeafGreen Version', 'system': 'Gameboy Advance'},
        {'name': 'Pokemon Diamond', 'system': 'Nintendo DS'},
        {'name': 'Pokemon Pearl', 'system': 'Nintendo DS'},
        {'name': 'Pokemon Platinum', 'system': 'Nintendo DS'},
        {'name': 'Pokemon HeartGold Version', 'system': 'Nintendo DS'},
        {'name': 'Pokemon SoulSilver Version', 'system': 'Nintendo DS'},
        {'name': 'Pokemon White', 'system': 'Nintendo DS'},
        {'name': 'Pokemon White Version 2', 'system': 'Nintendo DS'},
        {'name': 'Pokemon Black', 'system': 'Nintendo DS'},
        {'name': 'Pokemon Black Version 2', 'system': 'Nintendo DS'},
    ]

    loop = asyncio.get_event_loop()

    games = [Game(game) for game in game_list]
    games = loop.run_until_complete(fetch_all(games, loop))
    
    print(games)

    df = DataFrame.from_records(data=games)
    # df.loc["Total"] = to_numeric(df.sum(numeric_only=True, axis=0))

    print(df)
    df.to_csv('data/videogamepricer.csv', index=False)