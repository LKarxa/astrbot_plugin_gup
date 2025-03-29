import schedule
import time
import asyncio
import requests
import json
import os
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Plain

@register("stock_info", "YourName", "A plugin to fetch stock information from Sina Finance and send to QQ", "1.0.0")
class StockInfoPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.context = context
        self.config = config
        self.stock_code = config.get('stock_code', 'sh600000')  # 默认股票代码为上证指数
        self.schedule_job()

    def schedule_job(self):
        # 每日10:00获取股票信息并发送到QQ
        schedule.every().day.at("10:00").do(self.fetch_and_send_stock_info)

    @filter.command("set_stock")
    async def set_stock_command(self, event: AstrMessageEvent, stock_code: str):
        # 设置股票代码
        self.stock_code = stock_code
        self.config['stock_code'] = stock_code
        self.save_config()
        yield event.plain_result(f"股票代码已设置为: {stock_code}")

    @filter.command("get_stock")
    async def get_stock_command(self, event: AstrMessageEvent):
        # 获取当前设置的股票代码
        yield event.plain_result(f"当前股票代码为: {self.stock_code}")

    async def fetch_and_send_stock_info(self):
        # 获取股票信息，这里使用新浪财经的API作为示例
        url = f"http://hq.sinajs.cn/list={self.stock_code}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.text.split(',')
            current_price = data[3] if len(data) > 3 else 'N/A'
            message = f"当前{self.stock_code}股票价格: {current_price}"

            # 获取所有QQ群的unified_msg_origin
            groups = await self.context.get_all_groups()
            for group in groups:
                unified_msg_origin = group.unified_msg_origin
                await self.context.send_message(unified_msg_origin, [Plain(message)])

    @filter.command("stock")
    async def stock_command(self, event: AstrMessageEvent):
        # 手动触发获取股票信息
        await self.fetch_and_send_stock_info()
        yield event.plain_result("股票信息已发送到群聊。")

    def save_config(self):
        # 保存配置到文件
        config_path = os.path.join(self.context.data_dir, 'stock_info_config.json')
        with open(config_path, 'w') as f:
            json.dump(self.config, f)

# 初始化配置
def init_config(context):
    config_path = os.path.join(context.data_dir, 'stock_info_config.json')
    if not os.path.exists(config_path):
        with open(config_path, 'w') as f:
            json.dump({'stock_code': 'sh600000'}, f)
    with open(config_path, 'r') as f:
        return json.load(f)

# 运行定时任务
async def run_schedule():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

# 在插件启动时运行定时任务
async def on_startup():
    asyncio.create_task(run_schedule())

# 在插件关闭时停止定时任务
async def on_shutdown():
    schedule.clear()
