from functools import partial

import scrapy

from part2_regex import parse_dimensions
from part3_scrapy.items import ProductItemLoader


class BearspaceSpider(scrapy.Spider):
    name = 'bearspace'
    allowed_domains = ['bearspace.co.uk']
    start_urls = ['http://bearspace.co.uk/purchase']

    def parse(self, response, page=1):
        self.logger.info(f'Parsing page {page}')
        # Scrape all products on this page
        count = 0
        for link in response.xpath('//ul[@data-hook="product-list-wrapper"]/li//a[@data-hook="product-item-container"]/@href'):
            yield response.follow(link, self.parse_product)
            count += 1

        # If there are no products, it's the last page, we shall quit.
        if count == 0:
            self.logger.info(f'Finished scraping at page {page} - no products found')
            return

        # Follow to the next page.
        page += 1
        yield response.follow(f'http://bearspace.co.uk/purchase?page={page}', partial(self.parse, page=page))
        # Note: it's a crude way to form URL.
        # In production (especially if there are other parameters after ?) we may want to properly parse it
        # using `urllib` and change only "page" parameter.

    def parse_product(self, response):
        loader = ProductItemLoader(response=response)
        loader.add_value('url', response.url)
        loader.add_xpath('title', '//h1[@data-hook="product-title"]/text()')
        descriptions = response.xpath('//pre[@data-hook="description"]//p//text()').getall()
        # First we find dimensions (which line is it?)
        for i, description in enumerate(descriptions):
            try:
                dimensions = parse_dimensions(description)
                loader.add_value('height_cm', dimensions.height)
                loader.add_value('width_cm', dimensions.width)
                descriptions.pop(i)
                break
            except ValueError:
                pass
        # Note: we should do additional validation here
        if descriptions:
            loader.add_value('media', descriptions[0])
        loader.add_xpath('price_gbp', '//span[@data-hook="formatted-primary-price"]/text()')
        yield loader.load_item()
