# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup, NavigableString
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext, mirai
from pkg.plugin.events import *

@register(name="ImageSearchPlugin", description="使用识图网站搜索图片来源",
          version="1.0", author="BiFangKNT")
class ImageSearchPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        super().__init__(host)

    # 异步初始化
    async def initialize(self):
        pass

    @handler(PersonNormalMessageReceived)
    async def on_person_message(self, ctx: EventContext):
        await self.process_message(ctx)

    @handler(GroupNormalMessageReceived)
    async def on_group_message(self, ctx: EventContext):
        await self.process_message(ctx)

    async def process_message(self, ctx: EventContext):
        # 检查消息中是否包含图片
        message_chain = ctx.event.query.message_chain
        for message in message_chain:
            if isinstance(message, mirai.Image):
                image_url = message.url
                search_result = self.search_image(image_url)
                if search_result:
                    # 使用 add_return 方法添加回复
                    ctx.add_return('reply', [mirai.Plain(search_result)])
                    # 阻止该事件默认行为
                    ctx.prevent_default()
                break

    def search_image(self, image_url):
        try:
            url = "https://saucenao.com/search.php"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            }
            data = {'url': image_url, 'frame': '1', 'hide': '0', 'database': '999'}
            
            response = requests.post(url, data=data, headers=headers)

            if response.status_code == 200:
                return self.parse_result(response.text)
            else:
                return f"请求失败,状态码: {response.status_code}"
        except Exception as e:
            self.ap.logger.error(f"图片搜索失败: {str(e)}")
            return "图片搜索失败,请稍后再试。"

    def parse_result(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        result_div = soup.select_one('.resulttablecontent')
        
        if result_div:
            result = []

            # 处理 resulttitle
            title_div = result_div.select_one('.resulttitle')
            if title_div:
                strong = title_div.find('strong')
                if strong:
                    key = strong.text.strip(':')
                    next_sibling = strong.next_sibling
                    if next_sibling and isinstance(next_sibling, NavigableString):
                        value = next_sibling.strip()
                        result.append(f"{key} {value}")
                    else:
                        result.append(f"图片标题：{strong.text.strip()}")
                else:
                    result.append(f"图片标题：{title_div.text.strip()}")

            # 处理所有的 resultcontentcolumn
            content_columns = result_div.select('.resultcontentcolumn')
            for column in content_columns:
                strongs = column.find_all('strong')
                if strongs:
                    for strong in strongs:
                        key = strong.text.strip(':')
                        next_element = strong.next_sibling
                        value = ''
                        link_href = ''
                        while next_element:
                            if isinstance(next_element, NavigableString) and next_element.strip():
                                value = next_element.strip()
                                break
                            elif next_element.name == 'a' and next_element.has_attr('href'):
                                value = next_element.text.strip()
                                link_href = next_element['href']
                                break
                            next_element = next_element.next_sibling

                        if link_href:
                            result.append(f"{key} {value}(链接:{link_href})")
                        else:
                            result.append(f"{key} {value}")
                else:
                    value = column.text.strip()
                    link = column.find('a')
                    if link:
                        href = link.get('href', '')
                        result.append(f"{value}(链接:{href})")
                    else:
                        result.append(value)

            return "\n".join(result)
        else:
            return "未找到匹配的图片信息。"
    
    def __del__(self):
        pass
