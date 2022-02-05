import base64
import json
import os
from datetime import *
from io import BytesIO

from loguru import logger
from PIL import Image, ImageDraw, ImageFont


URL_3rdguide = "https://www.3rdguide.com/web/teamnew/index"
URL_nga = "https://bbs.nga.cn/thread.php?fid=549"


class HIAM(object):
    """HIAM"""

    @staticmethod
    def __savedb__():
        pass

    @staticmethod
    def __refresh__():
        exist = Abyss.__load__()
        temp = exist
        for item in list(temp):
            if datetime.fromtimestamp(float(exist[item]["endtime"])) < datetime.now():
                del exist[item]
        if exist is None:
            exist = {}
        HIAM.__dump__(exist)

    def __init__(self) -> None:
        super().__init__()
        self.__refresh__()

    @staticmethod
    def __load__() -> dict:
        hiampath = os.path.join(os.path.dirname(__file__), "HIAM.json")
        if not os.path.exists(hiampath):
            with open(hiampath, "w", encoding="utf8") as f:
                json.dump({}, f)
        with open(hiampath, "r", encoding="utf8") as f:
            try:
                data = json.load(f)
            except KeyError:
                data = {}
            f.close()
        return data

    @staticmethod
    def __dump__(data):
        with open(
            os.path.join(os.path.dirname(__file__), "HIAM.json"), "w", encoding="utf8"
        ) as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

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
    def __init__(self, weather: str = None, boss: str = None):
        """Abyss"""
        super().__init__()
        self.info = dict(self.get_data("abyss"))

        if (weather and boss) is None:
            try:
                data = self.__load__()["abyss"]
            except KeyError:
                data = {}
            if data == {}:
                raise KeyError(f"目前没有深渊数据")
            else:
                self.weather = data["weather"]
                self.boss = data["boss"]
                self.env = self.info[self.weather]["环境"]
                self.eff = self.info[self.weather]["效果"]
                self.endtime = datetime.fromtimestamp(data["endtime"])
                self.begintime = self.endtime + timedelta(days=-2)

                self.remain = (
                    str(self.endtime - datetime.today())[0:-4]
                    .replace("days", "天")
                    .replace("day", "天")
                )
        else:
            today = datetime.today()
            tw = today.isoweekday()
            tw = tw - 4 if tw > 4 else tw
            if tw == 4:
                raise ValueError(f"今天似乎是周四吧.")
            else:
                endtime = datetime(
                    today.year, today.month, today.day + (3 - tw), 22, 30, 0
                )
                self.begintime = endtime + timedelta(days=-2)
                self.endtime = endtime
                self.remain = (
                    str(self.endtime - datetime.today())[0:-4]
                    .replace("days", "天")
                    .replace("day", "天")
                )
                self.__setweather__(weather)
                self.__setboss__(boss)
                self.save()
                self.__clear__()

    def save(self):
        data = self.__load__()
        tosave = {
            "abyss": {
                "weather": self.weather,
                "boss": self.boss,
                "endtime": self.endtime.timestamp(),
            }
        }
        data.update(tosave)
        with open(
            os.path.join(os.path.dirname(__file__), "HIAM.json"), "w", encoding="utf8"
        ) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.close()

    def __setweather__(self, _weather):
        for w in self.info:
            if _weather == w or _weather == self.info[w]["环境"]:
                self.weather = w
                self.env = self.info[w]["环境"]
                self.eff = self.info[w]["效果"]
                self.list = self.info[w]["Boss"]
                return
        raise KeyError(f"不存在{_weather}天气的数据")

    def __setboss__(self, boss_name):
        t_name = self.trans_alias(boss_name)
        if t_name in self.list:
            self.boss = t_name
        else:
            raise KeyError(f"{boss_name}不在{self.weather}包含的boss{self.list}内")

    def __clear__(self):
        ims = os.listdir(os.path.join(os.path.dirname(__file__), "image/saved"))
        for im in ims:
            os.remove(os.path.join(os.path.dirname(__file__), f"image/saved/{im}"))

    @property
    def image(self):
        """以结束时间命名图片"""
        now = datetime.now()
        ims = os.listdir(os.path.join(os.path.dirname(__file__), "image/saved"))
        ims.sort(reverse=True)
        if ims:
            im = ims[0]
            im_name = im.split(".")[0]
            im_time = datetime.fromtimestamp(float(im_name))
            if im_time > now:
                return self.gen_image(
                    os.path.join(
                        os.path.dirname(__file__), f"image/saved/{im_name}.png"
                    )
                )
        return self.gen_image()

    @staticmethod
    def font(size, wenhei: bool = True):
        if wenhei:
            fontpath = os.path.join(os.path.dirname(__file__), "font/HYWenHei-65W.ttf")
        else:
            fontpath = os.path.join(os.path.dirname(__file__), "font/HYLingXinTiJ.ttf")
        return ImageFont.truetype(fontpath, size)

    def gen_image(self, im: str = None) -> str:
        """返回图片路径"""
        if not im:
            bg = Image.open(
                os.path.join(os.path.dirname(__file__), "image/bg.png")
            ).convert("RGBA")
            dr = ImageDraw.Draw(bg)
            dr.text(
                xy=(445, 54),
                text=f"{self.begintime.month}.{self.begintime.day}-{self.endtime.month}.{self.endtime.day}",
                fill="white",
                font=self.font(wenhei=False, size=36),
                anchor="mm",
            )
            dr.text(
                xy=(445, 125),
                text=f"{self.weather}-{self.env}环境",
                fill="white",
                font=self.font(size=30),
                anchor="mm",
            )
            effect = f"{self.eff}".split(",")
            for n, eff in enumerate(effect):
                dr.text(
                    xy=(445, 176 + n * 30),
                    text=eff,
                    fill="gray",
                    font=self.font(24),
                    anchor="mm",
                )
            dr.text(
                xy=(445, 526),
                text=f"{self.boss}",
                fill="red",
                font=self.font(30),
                anchor="mm",
            )
            boss_img = (
                Image.open(
                    os.path.join(os.path.dirname(__file__), f"image/{self.boss}.png")
                )
                .convert("RGBA")
                .resize(size=(551, 220))
            )
            bg.alpha_composite(boss_img, dest=(176, 274))
            im_path = os.path.join(
                os.path.dirname(__file__),
                f"image/saved/{int(self.endtime.timestamp())}.png",
            )
            bg.save(im_path, format="png")
        else:
            bg = Image.open(im).convert("RGBA")
            dr = ImageDraw.Draw(bg)
        dr.text(
            xy=(445, 601),
            text=f"{self.remain}",
            fill="white",
            font=self.font(30),
            anchor="lm",
        )
        # bg.show()
        bio = BytesIO()
        bg.save(bio, format="png", quality=100)
        base64_str = base64.b64encode(bio.getvalue()).decode()
        bg.close()
        return "base64://" + base64_str


if __name__ == "__main__":
    aby = Abyss(weather="虚数", boss="千律")
    # aby.weather = "点燃"
    # aby.boss = "丽塔"
    # aby.save()
    logger.debug(aby.endtime)
    aby.image
