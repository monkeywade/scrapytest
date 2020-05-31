import scrapy
from example.items import ExampleItem
from scrapy.linkextractors import LinkExtractor

class Bookspider(scrapy.Spider):
    name="books"
    start_urls=["http://books.toscrape.com/"]

    def parse(self, response):
        le = LinkExtractor(restrict_xpaths='//article/h3/a')
        links = le.extract_links(response)
        for link in links:
            yield scrapy.Request(link.url, callback=self.parse_book)

        le = LinkExtractor(restrict_xpaths='//li[@class="next"]')
        links = le.extract_links(response)
        for link in links:
            yield scrapy.Request(link.url, callback=self.parse)
        # next_url = links[0].url
        # yield scrapy.Request(next_url, callback=self.parse)

    def parse_book(self, response):
        book = ExampleItem()
        table = response.xpath('//article/table')
        book['name'] = response.xpath('//article//h1/text()').extract_first()
        book['price'] = table.xpath('//tr[3]/td/text()').extract_first()
        book['availability'] = table.xpath('//tr[6]/td/text()').re_first('(\d+)')
        book['review_num'] = table.xpath('//tr[7]/td/text()').extract_first()

        yield book
