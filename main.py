import sys, os, json, base64
import PIL
import rich
from datetime import *
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# sys.path.append(r'G:\GenshinTools\HoshinoBot')
# from hoshino import aiorequests

URL_3rdguide = "https://www.3rdguide.com/web/teamnew/index"
URL_nga = "https://bbs.nga.cn/thread.php?fid=549"


class HIAM(object):
    """HIAM"""

    def __init__(self) -> None:
        super().__init__()

    def get(self) -> dict:
        with open(
            os.path.join(os.path.dirname(__file__), "HIAM.json"), "r", encoding="utf8"
        ) as f:
            try:
                data = json.load(f)
            except KeyError:
                data = {}
            f.close()
        return data

    def get_data(self, type):
        DIRPATH = os.path.dirname(__file__)
        BOSS_PATH = {
            "abyss": os.path.join(DIRPATH, r"data/abyss.json"),
            "ma": os.path.join(DIRPATH, r"data/ma.json"),
        }
        with open(BOSS_PATH[type], "r", encoding="utf8") as f:
            weather_data = json.load(f)
            f.close()
        return weather_data

    def trans_alias(self, name):
        """转换别名"""
        with open(
            os.path.join(os.path.dirname(__file__), r"data/alias.json"),
            "r",
            encoding="utf8",
        ) as f:
            alias = json.load(f)
            f.close()
        for k, v in alias.items():
            if name in v or name == k:
                return k
        return False


class Abyss(HIAM):
    def __init__(self):
        """Abyss"""
        super().__init__()
        self.info = dict(self.get_data("abyss"))
        try:
            data = self.get()["abyss"]
        except KeyError:
            data = {}
        if data == {}:
            today = datetime.today()
            tw = today.isoweekday()
            tw = tw - 4 if tw > 4 else tw
            if tw == 4:
                raise ValueError(f"今天似乎是周四吧.")
            else:
                endtime = datetime(
                    today.year, today.month, today.day + (3 - tw), 22, 30, 0
                )
                self.endtime = endtime
                self._remain = str(self.endtime - datetime.today())[0:-4].replace(
                    "days", "天"
                )
        else:
            self._weather = data["weather"]
            self._boss = data["boss"]
            self.env = self.info[self._weather]["环境"]
            self.eff = self.info[self._weather]["效果"]
            self.endtime = datetime.fromtimestamp(data["endtime"])
            self._remain = str(self.endtime - datetime.today())[0:-4].replace(
                "days", "天"
            )

    @property
    def remain(self):
        self._remain = str(self.endtime - datetime.today())[0:-4].replace("days", "天")
        return self._remain

    def save(self):
        """ """
        data = self.get()
        tosave = {
            "abyss": {
                "weather": self._weather,
                "boss": self._boss,
                "endtime": self.endtime.timestamp(),
            }
        }
        data.update(tosave)
        with open(
            os.path.join(os.path.dirname(__file__), "HIAM.json"), "w", encoding="utf8"
        ) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.close()

    @property
    def weather(self):
        return self._weather

    @weather.setter
    def weather(self, _weather):
        for w in self.info:
            if _weather == w or _weather == self.info[w]["环境"]:
                self._weather = w
                self.env = self.info[w]["环境"]
                self.eff = self.info[w]["效果"]
                self.list = self.info[w]["Boss"]
                return
        raise KeyError(f"不存在{_weather}天气的数据")

    @property
    def boss(self):
        return self._boss

    @boss.setter
    def boss(self, boss_name):
        t_name = self.trans_alias(boss_name)
        if t_name in self.list:
            self._boss = t_name
        else:
            raise KeyError(f"{boss_name}不在{self._weather}包含的boss{self.list}内")


    def gen_image(self)->str:
        """返回base64图片"""
        if not (self.weather and self.boss):
            return

        font_path = r"G:\GenshinTools\HoshinoBot\res\font\NotoSansSC-Bold.otf"
        font_path1 = r"G:\GenshinTools\HoshinoBot\res\font\FZXiJinLJW.TTF"
        blank_image = Image.open(
            os.path.join(os.path.dirname(__file__), r"image/bg.png")
        )
        img_draw = ImageDraw.Draw(blank_image)
        fnt = ImageFont.truetype(font_path1, 40)
        fnt_s = ImageFont.truetype(font_path, 28)
        fnt_xs = ImageFont.truetype(font_path, 20)
        img_draw.text(xy=(10, 20), font=fnt, text=f"{self.weather}", fill=(232, 169, 0))

        img_draw.text(
            xy=(195, 200), font=fnt_s, text=f"{self.env}环境", fill=(255, 255, 255)
        )
        img_draw.text(
            xy=(195, 250), font=fnt_xs, text=f"{self.eff}", fill=(192, 192, 192)
        )
        img_draw.text(
            xy=(155, 300), font=fnt_s, text=f"主要敌人：{self._boss}", fill=(255, 255, 255)
        )
        img_draw.text(
            xy=(155, 480),
            font=fnt_s,
            text=f"距离结算还有：{self.remain}",
            fill=(255, 255, 255),
        )
        boss_img = Image.open(
            os.path.join(os.path.dirname(__file__), f"image/{self.boss}.png")
        ).convert("RGBA")
        r, g, b, a = boss_img.split()
        blank_image.paste(boss_img, (160, 350), mask=a)
        """以下pic2b64来自egenshin"""
        bio = BytesIO()
        data = blank_image.convert("RGB")
        data.save(bio, format="JPEG", quality=80)
        base64_str = base64.b64encode(bio.getvalue()).decode()
        return "base64://" + base64_str
        blank_image.show()


if __name__ == "__main__":
    aby = Abyss()
    # aby.weather = "点燃"
    # aby.boss = "丽塔"
    # aby.save()
    logger.debug(aby.endtime)
    aby.gen_image()
