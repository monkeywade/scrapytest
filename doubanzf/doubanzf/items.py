# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DoubanzfItem(scrapy.Item):
    # define the fields for your item here like:
    topic = scrapy.Field()
    author = scrapy.Field()
    release_time = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()