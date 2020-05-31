# coding: utf-8
from scrapy import cmdline
cmdline.execute(['scrapy', 'crawl', 'zufang', '-o', 'zufang.csv', '-s', 'FEED_EXPORT_ENCODING="utf_8_sig"'])
# cmdline.execute(['scrapy', 'crawl', 'zufang'])

