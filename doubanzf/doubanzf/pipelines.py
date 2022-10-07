# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem
import re


class DoubanzfPipeline(object):
    def __init__(self):
        self.book_set = set()

    def process_item(self, item, spider):
        # return item
        retain_content = '两房一厅|三房|2室1厅|2号线|二号线|一号线|1号线|2室2厅|2房2厅'
        drop_content = '合租|一室一厅|一房|限女|限男|招租|次卧|主卧|1室1厅|楼梯房'
        for content in item['content']:
            print(content)
            if re.search(drop_content, content):
                raise DropItem("Drop content found: %s" % item)
            elif re.search(retain_content, content):
                return item

# import pymysql.cursors
#
# class MySQLPipeline(object):
#     def __init__(self):
#         # 连接数据库
#         self.connect = pymysql.connect(
#             host='10.16.2.9',
#             port=33060,
#             db='zufang',
#             user='root',
#             passwd='mysql@2019',
#             charset='utf8mb4',
#             use_unicode=True)
#         # 开启游标cursor执行增删查改
#         self.cursor = self.connect.cursor()
#
#     def process_item(self, item, spider):
#         self.cursor.execute(
#             """CREATE TABLE IF NOT EXISTS house(
#             id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
#             topic VARCHAR(255) ,
#             author VARCHAR(255) ,
#             release_time VARCHAR(255) ,
#             url VARCHAR(255))""")
#         self.cursor.execute(
#             """insert into house(topic, author, release_time, url)
#             value (%s, %s, %s, %s)""",  # 这么写可防止sql注入攻击
#             (item['topic'],  # item里面定义的字段和表字段对应
#              item['author'],
#              item['release_time'],
#              item['url'],))
#
#         self.connect.commit()  # 提交sql语句
#         # self.connect.close()  # 关闭连接
#         # self.cursor.close()  # 关闭游标
#         return item