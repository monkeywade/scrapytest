# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from xiaohua.items import XiaohuaItem


class XiaohuaExampleSpider(scrapy.Spider):
    name = 'xiaohua'
    allowed_domains = ['www.521609.com']
    start_urls = ['http://www.521609.com/gaozhongxiaohua/']

    def start_requests(self):
        for i in range(1, 20):
            url = 'http://www.521609.com/xiaoyuanmeinv/list_%s.html'%i
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        le = LinkExtractor(restrict_xpaths='//div[@class="index_img list_center"]/ul/li/a')
        links = le.extract_links(response)

        for link in links:
            next_url = link.url
            yield scrapy.Request(next_url, callback=self.pic_parse)



    def pic_parse(self, response):
        item = XiaohuaItem()
        links = response.xpath('//div[@class="picbox"]/a/img/@src').extract()
        for link in links:
            #start_urls存放爬虫框架开始时的链接,该链接必须以列表形式存放,不能以字符串形式存放
            item['image_urls'] = [response.urljoin(link)]
            yield item
