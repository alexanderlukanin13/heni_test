# NOTE: here I suppose usage of `requests` is expected, so I demonstrated it via starting a local web server.
# You can run this script in console.
# If you want to view result in a Jupyter notebook, it can be easily adapted - `make_dataframe` function
# accepts file contents as str as an argument.


# Import modules.
# Idea: It's nice to structure modules in 3 groups: standard library, third-party, project-specific
import os
import time
import os.path as op
import re
import subprocess
import sys
from datetime import date, datetime
from io import StringIO

from lxml import html
import lxml.etree
import pandas as pd
import requests


class ScriptError(Exception):
    pass


class Loader:
    """A simple loader class, to avoid repeating ourselves."""

    def __init__(self, tree: lxml.etree._ElementTree):  # noqa
        self.tree = tree

    def get_first(self, xpath, *processors):
        """
        Extract first non-blank string matching xpath. Trim leading and trailing whitespace.
        If no match, return None.
        If there are optional processors, apply them one by one.
        Processor can be a one-argument callable or a regex string.
        If a regex string has groups (...), first group is extracted.
        """
        items = [x.strip() for x in self.tree.xpath(xpath) if x.strip()]
        if not items:
            return None
        result = items[0].strip()
        for processor in processors:
            if callable(processor):
                result = processor(result)
            else:
                if match := re.search(processor, result):
                    result = match.group(1) if match.groups() else match.group(0)
                else:
                    return None
        return result


def parse_price(s: str) -> int:
    """Parse price such as 'GBP 15,000,000' into integer."""
    if match := re.match(r'\s*(?:GBP|£|USD|$)\s*([0-9,]+)', s):
        return int(match.group(1).replace(',', ''))
    else:
        raise ValueError(f'Unexpected currency value: {s!r}')


def parse_price_range(s: str) -> tuple:
    """Parse price range into 2-tuple."""
    # If price range is in brackets (...), extract ... first
    if s.startswith('('):
        s = s.lstrip('(').split(')')[0]
    try:
        first, second = s.split('-')
        return parse_price(first), parse_price(second)
    except ValueError:
        raise ValueError(f'Unexpected currency range: {s!r}')

def parse_date(s: str) -> date:
    # NOTE: this is locale-dependent, so potentially fragile.
    # In a real task I'd use another method.
    return datetime.strptime(s, '%d %B %Y').date()


def make_dataframe(html_text: str) -> pd.DataFrame:
    tree = html.parse(StringIO(html_text))
    loader = Loader(tree)
    artist_name = loader.get_first('//h1[@class="lotName"]/text()', r'^[^(]+')  # 'Peter Doig (b. 1959)'
    # Note: we can also parse year of birth from here (and probably life years in other cases)
    lot_name = loader.get_first('//h2[@class="itemName"]//text()')
    # Note: For price, regexes can be more complex if other currencies are possible
    price_gbp = loader.get_first(
        '//span[@id="main_center_0_lblPriceRealizedPrimary"]/text()', parse_price)
    price_usd = loader.get_first(
        '//div[@id="main_center_0_lblPriceRealizedSecondary"]/text()', parse_price)

    price_gbp_est = loader.get_first(
        '//span[@id="main_center_0_lblPriceEstimatedPrimary"]/text()', parse_price_range
    )
    price_usd_est = loader.get_first(
        '//span[@id="main_center_0_lblPriceEstimatedSecondary"]/text()', parse_price_range
    )
    image_link = loader.get_first('//img[@id="imgLotImage"]/@src')
    sale_date = loader.get_first('//span[@id="main_center_0_lblSaleDate"]/text()', r'\d{1,2} \w+ \d{4}', parse_date)

    return pd.DataFrame(data={
        'artist_name': [artist_name],
        'lot_name': [lot_name],
        'price_gbp': [price_gbp],
        'price_usd': [price_usd],
        # Note: I'd make estimation two integer columns instead (min, max)
        'estimation_gbp': f'{price_gbp_est[0]}-{price_gbp_est[1]}',
        'estimation_usd': f'{price_usd_est[0]}-{price_usd_est[1]}',
        'image_link': [image_link],
        'sale_date': sale_date
    })


def do_request():
    """Do HTTP request, parse HTML and print Pandas dataframe."""
    html_page_link = 'candidateEvalData/webpage.html'
    try:
        response = requests.get(f'http://localhost:8000/{html_page_link}')
    except requests.exceptions.ConnectionError:
        raise ScriptError('Failed to connect to server')
    if response.status_code != 200:
        raise ScriptError(f'Server returned status {response.status_code}')
    df = make_dataframe(response.text)
    print(df.to_string())


def run_with_webserver():
    # To show usage of `requests`, we need a local web server.
    # Let's run it as a subprocess.
    # (another way would be to add custom adapter for `requests` and use 'file:///')
    server_process = None
    try:
        server_process = subprocess.Popen([
            sys.executable, '-m', 'http.server', '--bind', '127.0.0.1', '--directory', op.split(__file__)[0]
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)  # wait for server to be up; don't do this in production!
        do_request()
    finally:
        if server_process:
            server_process.terminate()


def main():
    try:
        run_with_webserver()
        return 0
    except ScriptError as ex:
        print(ex)
        return 1


if __name__ == '__main__':
    sys.exit(main())
