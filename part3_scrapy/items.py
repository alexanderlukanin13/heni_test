# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy.loader
from itemloaders.processors import TakeFirst, MapCompose

from part1_parsing import parse_price


class ProductItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    media = scrapy.Field()
    height_cm = scrapy.Field()
    width_cm = scrapy.Field()
    price_gbp = scrapy.Field()


def try_parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def try_parse_price(value):
    try:
        return parse_price(value)
    except ValueError:
        return None


def normalize_str(s):
    return s.strip()  # Note: we could also remove double whitespace, etc.


class ProductItemLoader(scrapy.loader.ItemLoader):
    default_item_class = ProductItem
    default_input_processor = MapCompose(normalize_str)
    default_output_processor = TakeFirst()

    height_cm_in = MapCompose(try_parse_float)
    width_cm_in = MapCompose(try_parse_float)
    price_gbp_in = MapCompose(try_parse_price)

    def load_item(self):
        item = super().load_item()
        # Product should at least have a title
        if not item['title']:
            raise ItemValidationError('Item has no title')
        return item


class ItemValidationError(Exception):
    """
    Loaded item is not valid.
    It may indicate that web page simply lacks data (so the item is unusable),
    or something is wrong with the spider.
    """
    pass
