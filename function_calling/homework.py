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




class MockedDB:
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
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    def initDB(self):
        # 创建orders表
        self.cursor.execute(self.database_schema_string)

        for record in self.mock_data:
            self.cursor.execute('''
            INSERT INTO products (product_name, product_price, product_volum, user_group)
            VALUES (?, ?, ?, ?)
            ''', record)
        # 提交事务
        self.conn.commit()
    def queryDB(self,sql):
        for row in self.cursor.execute(sql):
            print(row)

    def __init__(self):
        pass
    
    



def get_product(nul, model="gpt-3.5-turbo"):
    instruction='''
    based on one or more criteria, e.g. volume, price or user_group to search the best product that fit all criteria. If no any parameter provided, give me the lowest price one.
    '''
    messages= [
        {"role": "system", "content":instruction},
        {"role": "user", "content": nul}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.7,
        tool_choice="auto",
        tools=[{
                "type": "function",
                "function": {
                    "name": "search_product",
                    "description": "search product based on volume, price and user_group",
                    "parameters": {
                    "type": "object",
                    "properties": {
                        "volume": {
                            "type":"number",
                            "description":"the product volume"
                            },
                        "price":{
                           "type": "number",
                           "description":"the product price"
                            } ,
                        "user_group": {
                           "type": "string",
                           "description":"The product all which user to subscribed. If NULL then is no limited"
                          }
                    }
                    }
                }
        }]
    )
    # 如果返回的是函数调用结果，则打印出来
    if (response.tool_calls is not None):
    # 是否要调用 sum
        tool_call = response.tool_calls[0]
        if (tool_call.function.name == "sum"):
        # 调用 sum
            args = json.loads(tool_call.function.arguments)
            result = sum(args["numbers"])
            print("=====函数返回结果=====")
            print(result)

            # 把函数调用结果加入到对话历史中
            messages.append(
            {
                "tool_call_id": tool_call.id,  # 用于标识函数调用的 ID
                "role": "tool",
                "name": "sum",
                "content": str(result)  # 数值 result 必须转成字符串
            }
        )

        # 再次调用大模型
        print("=====最终 GPT 回复=====")
        #print(get_completion(messages).content)
    return response.choices[0].message

class NLU:
    instruction='''
            Based on user's description to a mobile plan product, to look up  a product that the most close to the user's requestion. 
            A product has properites:
            - volume: the data volume per month
            - price: the price of the product per month
            - user group: there are 3 user groups, Student, Business, Adual. 

            Rules:
            - if volume or price are not mentioned, use 'N/A'
            - Respond with json.
            '''

    def _get_completion(self, prompt, model="gpt-3.5-turbo"):
        messages = [ 
            {"role": "system", "content": self.instruction},
            {"role": "user", "content": prompt}
                    ]
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,  # 模型输出的随机性，0 表示随机性最小
            response_format={"type": "json_object"},
        )
        print(f"prompt={prompt}, generated nul={response.choices[0].message.content}.")
        semantics = json.loads(response.choices[0].message.content)
        return {k: v for k, v in semantics.items() if v}


def get_sql_completion(productJson, model="gpt-3.5-turbo"):
    messages = [
        {"role": "system", "content": "you are a helpful assistant that generates SQL queries from JSON objects"},
        {"role": "user", "content": productJson}
    ]
    tool = {
        "type": "function",
        "function": {
            "name": "ask_database",
            "description": "Use this function to answer user questions about business. \
                            Output should be a fully formed SQL query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": f"""
                        SQL query extracting info to answer the user's question.
                        SQL should be written using this database schema:
                        {MockedDB.database_schema_string}
                        The query should be returned in plain text, not in JSON.
                        The query should only contain grammars supported by SQLite.
                        """,
                    }
                }
            }
        }
    }

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        tools=[tool]
    )

    return response.choices[0].message


def search_product(volume, price,user_group):
    result=get_sql_completion(volume, price,user_group)
    return result

def main():
    #print('this is main')
    db =  MockedDB()
    db.initDB()
    db.queryDB("select * from products")
    nlu = NLU()
    nlu_responses = nlu._get_completion("I am in a university, I want to buy a 100G product")
    print(nlu_responses)
    #product=get_product(nlu)
    #print(product)

    
class DST:
    def __init__(self):
        pass

    def update(self, state, nlu_semantics):
        if "name" in nlu_semantics:
            state.clear()
        if "sort" in nlu_semantics:
            slot = nlu_semantics["sort"]["value"]
            if slot in state and state[slot]["operator"] == "==":
                del state[slot]
        for k, v in nlu_semantics.items():
            state[k] = v
        return state




if __name__ == "__main__":
    main()

class DialogManager:
    def __init__(self, prompt_templates):
        self.state = {}
        self.session = [
            {
                "role": "system",
                "content": "你是一个手机流量套餐的客服代表，你叫小瓜。可以帮助用户选择最合适的流量套餐产品。"
            }
        ]
        self.nlu = NLU()
        self.dst = DST()
        self.db = MockedDB()
        self.prompt_templates = prompt_templates

    def _wrap(self, user_input, records):
        if records:
            prompt = self.prompt_templates["recommand"].replace(
                "__INPUT__", user_input)
            r = records[0]
            for k, v in r.items():
                prompt = prompt.replace(f"__{k.upper()}__", str(v))
        else:
            prompt = self.prompt_templates["not_found"].replace(
                "__INPUT__", user_input)
            for k, v in self.state.items():
                if "operator" in v:
                    prompt = prompt.replace(
                        f"__{k.upper()}__", v["operator"]+str(v["value"]))
                else:
                    prompt = prompt.replace(f"__{k.upper()}__", str(v))
        return prompt

    def _call_chatgpt(self, prompt, model="gpt-3.5-turbo"):
        session = copy.deepcopy(self.session)
        session.append({"role": "user", "content": prompt})
        response = client.chat.completions.create(
            model=model,
            messages=session,
            temperature=0,
        )
        return response.choices[0].message.content

    def run(self, user_input):
        # 调用NLU获得语义解析
        semantics = self.nlu.parse(user_input)
        print("===semantics===")
        print(semantics)

        # 调用DST更新多轮状态
        self.state = self.dst.update(self.state, semantics)
        print("===state===")
        print(self.state)

        # 根据状态检索DB，获得满足条件的候选
        records = self.db.retrieve(**self.state)

        # 拼装prompt调用chatgpt
        prompt_for_chatgpt = self._wrap(user_input, records)
        print("===gpt-prompt===")
        print(prompt_for_chatgpt)

        # 调用chatgpt获得回复
        response = self._call_chatgpt(prompt_for_chatgpt)

        # 将当前用户输入和系统回复维护入chatgpt的session
        self.session.append({"role": "user", "content": user_input})
        self.session.append({"role": "assistant", "content": response})
        return response    
