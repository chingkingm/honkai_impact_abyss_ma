from hoshino import HoshinoBot, Service, typing,MessageSegment
import hoshino
from .main import *
sv = Service("HIAM",enable_on_default=False)

@sv.on_prefix("有人说深渊回答")
async def shenyuan(bot,ev:typing.CQEvent):
    abyss = Abyss()
    msg = ev.message.extract_plain_text().strip()
    try:
        abyss.weather = msg[0:2]
    except KeyError as e:
        await bot.send(ev,e)
        return
    try:
        abyss.boss = msg[2:]
    except KeyError as e:
        await bot.send(ev,e)
        return
    abyss.save()
    msg = MessageSegment.image(abyss.gen_image())
    await bot.send(ev,msg)

@sv.on_fullmatch("深渊")
async def show_abyss(bot,ev):
    abyss = Abyss()
    msg = MessageSegment.image(abyss.gen_image())
    await bot.send(ev,msg)
    





@sv.on_fullmatch("t1")
async def shenyuant(bot:HoshinoBot,ev:typing.CQEvent):
    abyss = Abyss()
    msg = MessageSegment.image(abyss.gen_image())
    await bot.send(ev,msg)