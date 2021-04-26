import locale

import regex
import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from pandas import DataFrame, to_numeric

locale.setlocale(locale.LC_ALL, '')

pricecharting_url = 'https://www.pricecharting.com/game'

games = [
    {'name': 'Pokemon Red', 'system': 'Gameboy'},
    {'name': 'Pokemon Blue', 'system': 'Gameboy'},
    {'name': 'Pokemon Yellow', 'system': 'Gameboy'},
    {'name': 'Pokemon Gold', 'system': 'Gameboy Color'},
    {'name': 'Pokemon Silver', 'system': 'Gameboy Color'},
    {'name': 'Pokemon Crystal', 'system': 'Gameboy Color'},
    {'name': 'Pokemon Ruby', 'system': 'Gameboy Advance'},
    {'name': 'Pokemon Sapphire', 'system': 'Gameboy Advance'},
    {'name': 'Pokemon Emerald', 'system': 'Gameboy Advance'},
    {'name': 'Pokemon Fire Red', 'system': 'Gameboy Advance'},
    {
        'name': 'Pokemon LeafGreen Version',
        'formatted_name': 'Pokemon Leaf Green',
        'system': 'Gameboy Advance',
    },
    {'name': 'Pokemon Diamond', 'system': 'Nintendo DS'},
    {'name': 'Pokemon Pearl', 'system': 'Nintendo DS'},
    {'name': 'Pokemon Platinum', 'system': 'Nintendo DS'},
    {
        'name': 'Pokemon HeartGold Version',
        'formatted_name': 'Pokemon HeartGold',
        'system': 'Nintendo DS',
    },
    {
        'name': 'Pokemon SoulSilver Version',
        'formatted_name': 'Pokemon SoulSilver',
        'system': 'Nintendo DS',
    },
    {'name': 'Pokemon White', 'system': 'Nintendo DS'},
    {
        'name': 'Pokemon White Version 2',
        'formatted_name': 'Pokemon White 2',
        'system': 'Nintendo DS',
    },
    {'name': 'Pokemon Black', 'system': 'Nintendo DS'},
    {
        'name': 'Pokemon Black Version 2',
        'formatted_name': 'Pokemon Black 2',
        'system': 'Nintendo DS',
    },
]


def formatForUrl(data: str):
    return '-'.join(data.lower().split())


def getPriceFromDiv(element: Tag) -> float:
    div_price: str = element.find('span', class_='price js-price').text.strip()
    div_price = regex.sub(r'[,$\s]+', '', div_price)

    if div_price == 'N/A':
        return

    value = locale.atof(div_price[1:])
    return value


game_data = []
for game in games:
    game_system = formatForUrl(game['system'])
    game_name = formatForUrl(game['name'])

    request_url = f'{pricecharting_url}/{game_system}/{game_name}'

    response = requests.get(url=request_url)

    soup = BeautifulSoup(response.content, 'html.parser')
    price_data_table: Tag = soup.find('table', id='price_data')

    try:
        loose_price_div: Tag = price_data_table.find('td', id='used_price')
        complete_price_div: Tag = price_data_table.find('td', id='complete_price')
        new_price_div: Tag = price_data_table.find('td', id='new_price')
        graded_price_div: Tag = price_data_table.find('td', id='graded_price')
        box_only_price_div: Tag = price_data_table.find('td', id='box_only_price')
        manual_only_price_div: Tag = price_data_table.find('td', id='manual_only_price')
    except AttributeError:
        print(f'Could not find {game["name"]}')
        break

    loose_price = getPriceFromDiv(loose_price_div)
    complete_price = getPriceFromDiv(complete_price_div)
    new_price = getPriceFromDiv(new_price_div)
    graded_price = getPriceFromDiv(graded_price_div)
    box_only_price = getPriceFromDiv(box_only_price_div)
    manual_only_price = getPriceFromDiv(manual_only_price_div)

    game_data.append(
        [
            game.get('formatted_name') or game['name'],
            loose_price,
            complete_price,
            new_price,
            graded_price,
            box_only_price,
            manual_only_price,
        ]
    )


df = DataFrame(
    data=game_data,
    columns=[
        'Game',
        'Loose',
        'Complete',
        'New',
        'Graded',
        'Box Only',
        'Manual Only',
    ],
)
df.loc["Total"] = to_numeric(df.sum(numeric_only=True, axis=0))
print(df)
