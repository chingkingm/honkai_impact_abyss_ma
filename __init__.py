import re
from hoshino import HoshinoBot, Service, typing, MessageSegment
from .main import Abyss
from .spider import Config

sv = Service("深渊战场boss", enable_on_default=True)

config = Config()


@sv.on_prefix("设置深渊")
async def set_abyss(bot: HoshinoBot, ev: typing.CQEvent):
    qid = ev.user_id
    if qid not in config.SU:
        return
    msg = ev.message.extract_plain_text().strip()
    regex = re.split(r"：|:|,|，", msg)
    if len(regex) > 1:
        weather, boss = regex[:2]
    else:
        weather = msg[:2]
        boss = msg[2:]
    try:
        abyss = Abyss(weather=weather, boss=boss)
    except Exception as e:
        await bot.send(ev, f"{e}")
        return
    msg = MessageSegment.image(abyss.image)
    await bot.send(ev, msg)


@sv.on_fullmatch("深渊")
async def show_abyss(bot, ev):
    try:
        abyss = Abyss()
    except Exception as e:
        await bot.send(ev, f"{e}")
        return
    msg = MessageSegment.image(abyss.image)
    await bot.send(ev, msg)


@sv.on_fullmatch("t1")
async def shenyuant(bot: HoshinoBot, ev: typing.CQEvent):
    abyss = Abyss()
    msg = MessageSegment.image(abyss.gen_image())
    await bot.send(ev, msg)

@sv.scheduled_job("cron",day_of_week="2,6",hour=20)
async def abyss_settle():
    abyss = Abyss()
    msg = f"今晚深渊结算\n{MessageSegment.image(abyss.image)}"
    sv.broadcast(msgs=msg)