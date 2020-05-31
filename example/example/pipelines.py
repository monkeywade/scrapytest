# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymysql.cursors

class MySQLPipeline(object):
    def __init__(self):
        # 连接数据库
        self.connect = pymysql.connect(
            host='172.16.169.237',
            port=32777,
            db='scrapybook',
            user='root',
            passwd='123456',
            charset='utf8mb4',
            use_unicode=True)
        # 开启游标cursor执行增删查改
        self.cursor = self.connect.cursor()

    def process_item(self, item, spider):
        item['price'] = float(item['price'][1:]) * 8.7591
        self.cursor.execute(
            """CREATE TABLE IF NOT EXISTS book(
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) , 
            price FLOAT(5), 
            availability INT(2), 
            review_num INT(3))""")
        self.cursor.execute(
            """insert into book(name, price, availability, review_num)
            value (%s, %s, %s, %s)""",  # 这么写可防止sql注入攻击
            (item['name'],  # item里面定义的字段和表字段对应
             item['price'],
             item['availability'],
             item['review_num'],))

        self.connect.commit()  # 提交sql语句
        # self.connect.close()  # 关闭连接
        # self.cursor.close()  # 关闭游标
        return item
