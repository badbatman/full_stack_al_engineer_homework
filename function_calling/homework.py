'''
名称	流量（G/月）	价格（元/月）	适用人群
经济套餐	10	50	无限制
畅游套餐	100	180	无限制
无限套餐	1000	300	无限制
校园套餐	200	150	在校生
'''
# 初始化
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import json
import sqlite3

_ = load_dotenv(find_dotenv())

client = OpenAI()
#  描述数据库表结构
database_schema_string = """
CREATE TABLE products (
    product_name STR NOT NULL, -- product name
    product_price DECIMAL(10,2) NOT NULL, -- product price per month
    product_volum INT NOT NULL, -- volume per month
    user_group STR, -- The product all which user to subscribed. If NULL then is no limited.
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- record created timestamp
    
);
"""

# 插入5条明确的模拟记录
mock_data = [
    ('经济套餐', 50.00,10,None),
    ('畅游套餐', 180.00, 100,None),
    ('无限套餐', 300.00, 1000,None),
    ('校园套餐', 150.00, 200,'Student')
    
]

# 创建数据库连接
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

def initDB():
    # 创建orders表
    cursor.execute(database_schema_string)

    for record in mock_data:
        cursor.execute('''
        INSERT INTO products (product_name, product_price, product_volum, user_group)
        VALUES (?, ?, ?, ?)
        ''', record)
    # 提交事务
    conn.commit()

def queryDB(sql):
    for row in cursor.execute(sql):
        print(row)


def main():
    print('this is main')
    initDB()
    queryDB("select * from products")



if __name__ == "__main__":
    main()

    
