# -*- coding: utf-8 -*-

# Scrapy settings for doubanzf project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'doubanzf'

SPIDER_MODULES = ['doubanzf.spiders']
NEWSPIDER_MODULE = 'doubanzf.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'doubanzf (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
'Accept-Language': 'zh-CN,zh;q=0.9',
'Cookie': 'll="118282"; bid=tf0ws8R1hR8; __utmz=30149280.1661431546.1.1.utmcsr=baidu|utmccn=(organic)|utmcmd=organic; __gads=ID=82bf2419131d26fd-224f045cd0d500da:T=1661431547:RT=1661431547:S=ALNI_MaLpNF9n7Ku-7vuZrx5cIM7PWraWA; __yadk_uid=3ZBJzhqPowZd4gaZdnFFD549MGUYPc37; __utmc=30149280; __gpi=UID=00000907c0515d18:T=1661431547:RT=1665107772:S=ALNI_MY1PATcfyXR7g4_w5Kn_cKTyYapVQ; ct=y; dbcl2="202797008:uVkbaGSektk"; ck=Gqix; push_noty_num=0; push_doumail_num=0; __utmv=30149280.20279; frodotk_db="e1f9fdc4fede5edca5edf94efc9b1c94"; _pk_ses.100001.8cb4=*; __utma=30149280.1851959539.1661431546.1665107768.1665117388.3; __utmt=1; _pk_id.100001.8cb4=a23f7e9f239730da.1665107767.2.1665117803.1665115346.; __utmb=30149280.28.5.1665117803828',
'Host': 'www.douban.com',
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Core/1.94.169.400 QQBrowser/11.0.5130.400'
}

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'doubanzf.middlewares.DoubanzfSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'doubanzf.middlewares.DoubanzfDownloaderMiddleware': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # 'doubanzf.pipelines.MySQLPipeline': 100,
    'doubanzf.pipelines.DoubanzfPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
