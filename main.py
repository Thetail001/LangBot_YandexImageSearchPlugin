# -*- coding: utf-8 -*-
import asyncio
import base64
import tempfile
from pkg.plugin.context import register, handler, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
import pkg.platform.types as platform_types
from PicImageSearch import Network, Yandex
from PicImageSearch.model import YandexResponse

@register(name="YandexImageSearchPlugin", description="使用Yandex搜索图片来源",
          version="1.0", author="Thetail")
class ImageSearchPlugin(BasePlugin):

    def __init__(self, host: APIHost):
        super().__init__(host)

    # 异步初始化
    async def initialize(self):
        pass

    @handler(PersonNormalMessageReceived)
    @handler(GroupNormalMessageReceived)
    async def on_message(self, ctx: EventContext):
        await self.process_message(ctx)

    async def process_message(self, ctx: EventContext):
        """处理收到的消息"""
        self.ap.logger.info("开始处理消息。")
        message_chain = ctx.event.query.message_chain
        self.ap.logger.info(f"message_chain 内容: {message_chain}")
        self.ap.logger.info(f"message_chain 长度: {len(message_chain)}")
        for message in message_chain:
            if isinstance(message, platform_types.Image):
                self.ap.logger.info("message, platform_types.Image")
                if message.base64:
                    self.ap.logger.info("message.base64")
                    temp_image_path = self.save_base64_image(message.base64)
                    try:
                        if temp_image_path:
                            search_result = await asyncio.shield(self.search_image(temp_image_path))
                            if search_result:
                                ctx.add_return('reply', search_result)
                                ctx.prevent_default()
                                ctx.prevent_postorder()
                        else:
                            self.ap.logger.error("图片保存失败，无法进行搜索。")
                    finally:
                        # 确保临时文件被删除
                        if temp_image_path:
                            import os
                            os.remove(temp_image_path)
                else:
                    self.ap.logger.error("No Base64 image data found.")

    def save_base64_image(self, base64_data):
        """将 Base64 编码的图片数据保存为临时文件"""
        try:
            # 创建临时文件，后缀为 .jpg
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                # 去掉 Base64 头部信息（如 data:image/jpeg;base64,）
                header, encoded = base64_data.split(",", 1) if "," in base64_data else ("", base64_data)
                
                # 解码 Base64 数据
                image_data = base64.b64decode(encoded)
                
                temp_file.write(image_data)
                temp_file.flush()  # 确保数据写入磁盘
                self.ap.logger.info(f"图片已保存到临时文件: {temp_file.name}")
                
                # 返回临时文件路径
                return temp_file.name
        except Exception as e:
            self.ap.logger.error(f"解析 Base64 图片失败: {e}")
            return None      
          
    async def search_image(self, temp_image_path):
        """ 使用 PicImageSearch 进行 Yandex 以图搜图 """
        try:
            async with Network() as client:
                yandex = Yandex(client=client)
                self.ap.logger.info(f"temp_file_path： {temp_image_path}")      
                resp = await yandex.search(file=temp_image_path)
                return self.parse_result(resp)
        except Exception as e:
            self.ap.logger.error(f"图片搜索失败: {str(e)}")
            return [platform_types.Plain("图片搜索失败，请稍后再试。")]

    def parse_result(self, resp: YandexResponse):
        """ 解析 Yandex 搜索结果 """
        if not resp.raw:
            self.ap.logger.error("未找到匹配的搜索结果")
            return [platform_types.Plain("未找到匹配的图片信息。")]

        first_result = resp.raw[0]  # 取第一个搜索结果

        # 生成消息内容
        message_parts = [
            platform_types.Plain(
                f"🔍 **Yandex 搜索结果**\n"
                f"📌 **标题**: {first_result.title}\n"
                f"🔗 **链接**: {first_result.url}\n"
                f"📍 **来源**: {first_result.source}\n"
                f"📄 **描述**: {first_result.content}\n"
                f"📏 **尺寸**: {first_result.size}\n"
            )
        ]

        # 添加缩略图作为图片
        if first_result.thumbnail:
            message_parts.append(platform_types.Image(url=first_result.thumbnail))

        return message_parts  # 返回列表

    def __del__(self):
        pass
