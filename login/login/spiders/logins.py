# -*- coding: utf-8 -*-
import scrapy

class LoginsSpider(scrapy.Spider):
    name = 'logins'
    allowed_domains = ['b.edu.51cto.com']
    start_urls = ['http://b.edu.51cto.com/unicom/course/index']


    def parse(self, response):
        print(response.text)
        # print(response.xpath('//title/text()').extract())
#
