# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from chemotu.items import ChemotuItem
import re

class ChemoSpider(scrapy.Spider):
    name = 'chemo'
    allowed_domains = ['www.mm131.net']
    start_urls = ['http://www.mm131.net/chemo/', 'https://www.mm131.net/xinggan/', 'https://www.mm131.net/qingchun/',
                  'https://www.mm131.net/xiaohua/', 'https://www.mm131.net/qipao/', 'https://www.mm131.net/mingxing/']

    def parse(self, response):
        le = LinkExtractor(restrict_xpaths='//dl[@class="list-left public-box"]/dd[@class="page"]/a')
        links = le.extract_links(response)
        first_url = self.start_urls
        for link in links:
            first_url.append(link.url)
            for f_url in first_url:
                yield scrapy.Request(f_url, callback=self.first_url_parse)

    def first_url_parse(self,response):
        # 不选择属性值为page的节点——dd[not(@class="page")]
        le = LinkExtractor(restrict_xpaths='//dl[@class="list-left public-box"]/dd[not(@class="page")]/a')
        links = le.extract_links(response)
        for link in links:
            # print(link.url)
            yield scrapy.Request(link.url, callback=self.url_parse)


    def url_parse(self, response):
        item = ChemotuItem()
        item['images'] = response.xpath('//div[@class="content"]/h5/text()').extract_first()
        num_str = response.xpath('//span[@class="page-ch"]/text()').extract_first()
        num = re.findall(r"\d+", num_str)
        for i in range(2,int(" ".join(num))+1):
            # format方法传入页码，获取相应网址
            url = response.url.replace(".html", "_{}.html").format(i)
            yield scrapy.Request(url, meta={'name':item['images']}, callback=self.pic_parse)

    def pic_parse(self, response):
        img_links = response.xpath('//div[@class="content-pic"]/a/img/@src').extract()
        item = ChemotuItem()
        item['image_urls'] = img_links
        item['images'] = response.meta['name']
        yield item