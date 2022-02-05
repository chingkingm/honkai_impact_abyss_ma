# 本质是个爬虫
# pylint: disable=no-name-in-module
# pylint: disable=no-self-argument
import asyncio
import json
import os
import re
import time
from datetime import datetime
from typing import List, Optional

import hoshino
from bs4 import BeautifulSoup
from hoshino import HoshinoBot, MessageSegment, Service, aiorequests, priv
from hoshino.typing import CQEvent
from pydantic import BaseModel
from selenium import webdriver

sv = Service("崩坏3深渊战场速报",enable_on_default=False)
NGA = "https://bbs.nga.cn/thread.php?fid=549"

class Config():
    @staticmethod
    def __load__(path:str="spider_config.json"):
        with open(os.path.join(os.path.dirname(__file__),path),"r",encoding='utf8') as configfile:
            data = json.load(configfile)
            configfile.close()
        return data
    @staticmethod
    def dump(data):
        nowdata = Config.__load__()
        with open(os.path.join(os.path.dirname(__file__),"spider_config.json"),"w",encoding='utf8') as configfile:
            nowdata.update(data)
            json.dump(nowdata,configfile,indent=4,ensure_ascii=False)
            configfile.close()
    def __init__(self) -> None:
        data = self.__load__()
        self.SU = set(hoshino.config.SUPERUSERS).union(data["SU"])
        self.groups = data["enable_push_group"]
        self._abyss = data["abyss"] if "abyss" in data else None
        self.memory = data["memory"] if "memory" in data else None

    @property
    def abyss(self):
        return self._abyss
    @abyss.setter
    def abyss(self,weather,boss,img):
        self._abyss = {
            "weather":weather,
            "boss":boss,
            "img":img
        }
        self.dump(self._abyss)
    @property
    def ma(self):
        return self._ma
    @ma.setter
    def ma(self,boss,img):
        self._ma = {
            "boss":boss,
            "img":img
        }
        self.dump(self._ma)
class _NGACookie(BaseModel):
    domain:str
    expiry:Optional[datetime]
    httpOnly:bool
    name:str
    path:str
    secure:bool
    value:str
class NGACookies(BaseModel):
    cookies:List[_NGACookie]
    def output(self):
        """输出cookies"""
        ret = {}
        for ck in self.cookies:
            ret.update({ck.name:ck.value})
        return ret
class NGAarticle():
    def __init__(self,tid:str,title:str) -> None:
        self.tid = tid
        self.title = title
        self.url = f"https://bbs.nga.cn/read.php?tid={self.tid}"
        self.imgs = []
    def __repr__(self) -> str:
        return f"{self.title}:\n{self.url}\n"
    def cache(self):
        """key:self.tid"""
        exists_article = Config.__load__()["pushed"]
        assert isinstance(exists_article,list)
        exists_article.append(self.tid)
        Config.dump({"pushed":exists_article})
    def isincache(self):
        exists_article = Config.__load__()["pushed"]
        return self.tid in exists_article
    async def get_content(self,cookie):
        """获取帖子主楼内容"""
        resp = await aiorequests.get(url=self.url,cookies=cookie)
        soup = BeautifulSoup(await resp.content,'html5lib')
        mainfloor = soup.find("tr",id="post1strow0")
        content = mainfloor.find("p",id="postcontent0")
        cmd_text = content.get_text()
        img = re.findall(r"\[img\][a-zA-Z_\-\d/.]{1,}\[/img\]|\[s:[\w:]+\]",cmd_text)
        if img is not None:
            for im in img:
                temp = '.'
                if im.startswith("[img]"):
                    temp = f"https://img.nga.178.com/attachments/{im[7:-6]}"
                    self.imgs.append(temp)
                    temp = f"{MessageSegment.image(temp)}"
                cmd_text = cmd_text.replace(im,temp)
        tags = re.findall(r"\[/?(h|list|collapse|\*|quote|url)\]",cmd_text)
        for tag in tags:
            cmd_text = cmd_text.replace(tag,"")
        return cmd_text
def get_nga_cookie():
    driver = webdriver.Chrome()
    driver.get(url=NGA)
    time.sleep(5)
    cookie = driver.get_cookies()
    cks = NGACookies(**{'cookies':cookie})
    driver.close()
    return cks.output()
async def spider(bot:HoshinoBot,re_string:str):
    cookie = get_nga_cookie()
    resp = await aiorequests.get(url=NGA,cookies=cookie)
    soup = BeautifulSoup(await resp.content,'html5lib')
    topic = soup.find_all(class_="topic")
    hitbox = []
    for result in topic:
        try:
            tid = result["href"].split("=")[1]
        except IndexError:
            continue
        title = result.get_text()
        if "YYGQ" in title:
            continue
        if re.search(re_string,title):
            art = NGAarticle(tid, title)
            hitbox.append(art)
    if "深渊" in re_string:
        re_string = "深渊"
    elif "战场" in re_string:
        re_string = "战场"
    else:
        re_string = "测试"
    if hitbox == []:
        return None
    ret_text = ''
    config = Config()
    for n,article in enumerate(hitbox):
        assert isinstance(article,NGAarticle)
        if article.isincache():
            continue
        article.cache()
        ret_text = f"{ret_text}{n}.{article}"
        su_msg = await article.get_content(cookie)
        # 向SU及启用了推送的群发送详细信息
        for su in config.SU:
            await bot.send_private_msg(user_id=int(su),message=f"{n}.{article}{su_msg}")
            await asyncio.sleep(0.5)
        for group in config.groups:
            if group not in sv.enable_group:
                continue
            await bot.send_group_msg(group_id=int(group),message=f"{n}.{article}{su_msg}")
            await asyncio.sleep(1)
    # 向启用了插件的群发送简略信息
    await asyncio.sleep(2)
    if ret_text == "":
        return
    for group in sv.enable_group:
        if group in config.groups:
            continue
        await bot.send_group_msg(group_id=int(group),message=f"{re_string[:2]}速报\n{ret_text}")
        await asyncio.sleep(1)
@sv.scheduled_job('cron',second='30',minute='0-20', hour='15', day_of_week='0,4')
async def fetch_abyss():
    bot = hoshino.get_bot()
    await spider(bot,r"深渊([速慢]报)?")

@sv.scheduled_job('cron',second='30',minute='0-10', hour='8', day_of_week='1')
async def fetch_ma():
    bot = hoshino.get_bot()
    await spider(bot,r"战场([速慢]报)?")
@sv.on_suffix("深渊战场推送")
async def on_off(bot:HoshinoBot,ev:CQEvent):
    msg = ev.message.extract_plain_text().strip()
    group = ev.group_id
    if not priv.check_priv(ev,priv.ADMIN):
        return
    config = Config()
    enable_group = set(config.groups)
    if msg in ["启用","开启"] and group not in enable_group:
        enable_group.add(group)
        config.dump({"enable_push_group":list(enable_group)})
        await bot.send(ev,f"启用成功.")
    elif msg in ["禁用","关闭"]:
        try:
            enable_group.remove(group)
            config.dump({"enable_push_group":list(enable_group)})
            await bot.send(ev,f"禁用成功.")
        except:
            return

@sv.on_prefix("testpac")
async def testpac(bot,ev):
    if not priv.check_priv(ev,priv.SUPERUSER):
        return
    msg = ev.message.extract_plain_text().strip()
    await spider(bot,msg)

if __name__ == '__main__':
    # asyncio.run(mm())
    pass
