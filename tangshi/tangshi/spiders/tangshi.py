import scrapy
from tangshi.items import TangshiItem
import re
from copy import deepcopy

class Tanshispider(scrapy.Spider):
    name="tangshi"
    start_urls=["https://www.gushiwen.org/gushi/tangshi.aspx"]

    def parse(self, response):
        result = TangshiItem()
        typeconts = response.xpath('//div[@class="typecont"]')
        for typecont in typeconts:
            result['category'] = typecont.xpath('./div/strong/text()').extract_first()
            spans = typecont.xpath('.//span')
            for span in spans:
                result['name'] = span.xpath('./a/text()').extract_first()
                result['author'] = span.xpath('./text()').re(r'[(](.*?)[)]', re.S)
                result['url'] = span.xpath('./a/@href').extract_first()
                yield scrapy.Request(url=result['url'], meta={'item': deepcopy(result)}, callback=self.parse_book)

                # yield result

    def parse_book(self, response):
        item = response.meta['item']
        item['content'] = response.xpath('//div[@class="contson"]')[0].xpath('.//text()').extract()
        yield item
