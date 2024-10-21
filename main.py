# -*- coding: utf-8 -*-
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext, mirai
from pkg.plugin.events import PersonNormalMessageReceived, GroupNormalMessageReceived

@register(name="ImageSearchPlugin", description="使用识图网站搜索图片来源",
          version="1.0", author="BiFangKNT")
class ImageSearchPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        super().__init__(host)
        self.driver = None

    async def initialize(self):
        # 初始化Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        self.driver = webdriver.Chrome(options=options)

    @handler(PersonNormalMessageReceived)
    async def on_person_message(self, ctx: EventContext):
        await self.process_message(ctx)

    @handler(GroupNormalMessageReceived)
    async def on_group_message(self, ctx: EventContext):
        await self.process_message(ctx)

    async def process_message(self, ctx: EventContext):
        # 检查消息中是否包含图片
        if ctx.query and ctx.query.message_chain:
            for message in ctx.query.message_chain:
                if isinstance(message, mirai.Image):
                    image_url = message.url
                    search_result = self.search_image(image_url)
                    if search_result:
                        await ctx.send(search_result)
                    break

    def search_image(self, image_url):
        try:
            self.driver.get("https://saucenao.com/")
            
            # 上传图片
            file_input = self.driver.find_element(By.XPATH, '/html/body/div/div[1]/div[3]/form/div[1]/div/input')
            file_input.send_keys(image_url)
            
            # 点击搜索按钮
            search_button = self.driver.find_element(By.XPATH, '/html/body/div/div[1]/div[3]/form/div[2]/input')
            search_button.click()
            
            # 等待结果加载
            result_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div[2]/table/tbody/tr/td[2]/div[2]'))
            )
            
            # 获取结果信息
            author = result_div.find_element(By.XPATH, './div[1]').text
            source_link = result_div.find_element(By.XPATH, './div[2]/a').get_attribute('href')
            original_work = result_div.find_element(By.XPATH, './div[2]').text
            characters = result_div.find_element(By.XPATH, './div[3]').text
            
            return f"作者: {author}\n原作: {original_work}\n角色: {characters}\n链接: {source_link}"
        
        except Exception as e:
            self.ap.logger.error(f"图片搜索失败: {str(e)}")
            return "图片搜索失败,请稍后再试。"

    def __del__(self):
        if self.driver:
            self.driver.quit()
