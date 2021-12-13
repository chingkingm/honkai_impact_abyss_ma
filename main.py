import sys,os,json
import rich
from loguru import logger
# sys.path.append(r'G:\GenshinTools\HoshinoBot')
# from hoshino import aiorequests

URL_3rdguide = 'https://www.3rdguide.com/web/teamnew/index'
URL_nga = 'https://bbs.nga.cn/thread.php?fid=549'

class HIAM(object):
    """HIAM"""
    def __init__(self) -> None:
        super().__init__()

    def get_data(self,type):
        DIRPATH = os.path.dirname(__file__)
        BOSS_PATH = {
            "abyss": os.path.join(DIRPATH,r'data/abyss.json'),
            "ma":os.path.join(DIRPATH,r'data/ma.json')
        }
        with open(BOSS_PATH[type],'r',encoding='utf8') as f:
            weather_data = json.load(f)
            f.close()
        return weather_data       

    def trans_alias(self,name):
        """转换别名"""
        with open(os.path.join(os.path.dirname(__file__),r'data/alias.json'),'r',encoding='utf8') as f:
            alias = json.load(f)
            f.close()
        for k,v in alias.items():
            if name in v or name == k:
                return k
        return False
    
           
class Abyss(HIAM):
    def __init__(self) -> None:
        """Abyss"""
        super().__init__()
        self.info = dict(self.get_data('abyss'))
    
    @property
    def weather(self):
        return self._weather
    @weather.setter
    def weather(self,_weather):
        for w in self.info:
            if _weather == w or _weather == self.info[w]["环境"]:
                self._weather = w
                self.eff = self.info[w]["效果"]
                self.list = self.info[w]["Boss"]
            else:
                return f'不存在{_weather}天气的数据'

    @property
    def boss(self):
        return self._boss
    @boss.setter
    def boss(self,boss_name):
        t_name = self.trans_alias(boss_name)
        if t_name in self.list:
            self._boss = t_name
        else:
            raise KeyError(f'{boss_name}不在{self._weather}包含的boss{self.list}内')

if __name__ == '__main__':
    aby = Abyss()
    aby.weather = '雷电'
    logger.debug(aby.eff)
    aby.boss = "呆鹅"
    pass
