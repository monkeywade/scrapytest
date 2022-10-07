# -*- coding: utf-8 -*-
import scrapy
from doubanzf.items import DoubanzfItem
from scrapy.linkextractors import LinkExtractor


class ZufangSpider(scrapy.Spider):
    name = 'zufang'
    allowed_domains = ['www.douban.com']
    start_urls = []

    for i in range(0, 250, 25):
        # start_urls.append('https://www.douban.com/group/nanshanzufang/discussion?start=%s' % i)
        start_urls.append('https://www.douban.com/group/futianzufang/discussion?start=%s&type=new' % i)
        # start_urls.append('https://www.douban.com/group/586502/discussion?start=%s'%i)

    def parse(self, response):
        le = LinkExtractor(restrict_xpaths='//table[@class="olt"]//td[@class="title"]/a')
        links = le.extract_links(response)
        for link in links:
            yield scrapy.Request(link.url, callback=self.cont_parse)

    def cont_parse(self, response):
        book = DoubanzfItem()
        contents = response.xpath('//div[@class="topic-doc"]')

        book['topic'] = response.xpath('//div[@id="content"]/h1/text()').extract_first()
        book['author'] = contents.xpath('./h3/span/a/text()').extract_first()
        book['release_time'] = contents.xpath('./h3/span[@class="create-time color-green"]/text()').extract_first()
        book['url'] = response.url
        book['content'] = contents.xpath('.//div[@class="rich-content topic-richtext"]//text()').extract()
        # print(book)
        yield book


