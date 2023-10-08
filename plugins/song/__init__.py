from .netease_music_api import search_song as searchSongNeteaseAPI

from typing import Union, Any, List, Dict, Tuple
from utils.standard_plugin import StandardPlugin
from utils.basic_event import send, warning, gocq_quote
from utils.basic_configs import SAVE_TMP_PATH, ROOT_PATH
from utils.response_image_beta import *
import re
import json
import time


def aio_get_avatar(imgUrls: List[str]) -> List:
    pass


def netease_id_to_url(songId: int) -> str:
    return f'https://music.163.com/#/song?id={songId}'


def dump_song_info(songInfos: List[Dict]) -> Tuple[bool, str]:
    try:
        result = []
        for songIdx, songInfo in enumerate(songInfos):
            name = gocq_quote(songInfo['name'])
            songId = songInfo['id']
            songUrl = gocq_quote(netease_id_to_url(songId))
            result.append(f'{songIdx + 1}. {name} {songUrl}')
        return True, '\n'.join(result)
    except BaseException as e:
        warning('exception in dumpSongInfo: {}'.format(e))
        return False, str(e)


def draw_song_info(songInfos: List[Dict], savePath: str) -> Tuple[bool, str]:
    try:
        songCard = ResponseImage(
            titleColor=PALETTE_SJTU_BLUE,
            title='小马点歌',
            layout='normal',
            width=880,
            cardBodyFont=ImageFont.truetype(os.path.join(FONTS_PATH, '汉仪文黑.ttf'), 60),
            cardTitleFont=ImageFont.truetype(os.path.join(FONTS_PATH, 'SourceHanSansCN-Medium.otf'), 26),
            cardSubtitleFont=ImageFont.truetype(os.path.join(FONTS_PATH, 'SourceHanSansCN-Medium.otf'), 20),
        )
        for songIdx, songInfo in enumerate(songInfos):
            name = songInfo['name']
            songId = songInfo['id']
            duration = int(songInfo['dt'] / 1000)
            durMin = duration // 60
            durSec = duration % 60
            albumName = songInfo['al']['name']
            picReq = requests.get(songInfo['al']['picUrl'])
            if picReq.status_code == requests.codes.ok:
                pic = Image.open(BytesIO(picReq.content))
            else:
                pic = None
            authorName = songInfo['ar'][0]['name']
            songCard.add_card(
                ResponseImage.RichContentCard(
                    raw_content=[
                        ('title', f'{songIdx + 1}. {name}'),
                        ('subtitle', f'ID:  {songId}', PALETTE_GREY_SUBTITLE),
                        ('subtitle', f'作者: {authorName}', PALETTE_GREY_SUBTITLE),
                        ('subtitle', f'专辑: {albumName}', PALETTE_GREY_SUBTITLE),
                        ('subtitle', f'时长: %02d:%02d' % (durMin, durSec), PALETTE_GREY_SUBTITLE),
                    ],
                    icon=pic
                )
            )
        songCard.generate_image(savePath)
        return True, savePath
    except BaseException as e:
        warning('exception in drawSongInfo: {}'.format(e))
        return False, str(e)


class ChooseSong(StandardPlugin):
    def __init__(self) -> None:
        self.pattern = re.compile('^点歌\s+(\S.*)$')

    def judge_trigger(self, msg: str, data) -> bool:
        return self.pattern.match(msg) != None

    def execute_event(self, msg: str, data) -> Union[None, str]:
        target = data['group_id'] if data['message_type'] == 'group' else data['user_id']
        songName = self.pattern.findall(msg)
        try:
            try:
                songInfos = searchSongNeteaseAPI(songName)[:5]
            except:
                try:
                    time.sleep(0.5)
                    songInfos = searchSongNeteaseAPI(songName)[:5]
                except:
                    time.sleep(1)
                    songInfos = searchSongNeteaseAPI(songName)[:5]

            if len(songInfos) == 0:
                send(target, '[CQ:reply,id=%d]搜索结果为空' % (data['message_id'],), data['message_type'])
            else:
                savePath = os.path.join(ROOT_PATH, SAVE_TMP_PATH, 'song_%d.png' % target)
                if draw_song_info(songInfos, savePath)[0]:
                    send(target, '[CQ:image,file=files:///%s]' % savePath, data['message_type'])
                    dumpOK, songText = dump_song_info(songInfos)
                    if dumpOK:
                        send(target, songText, data['message_type'])
                else:
                    send(target, '[CQ:reply,id=%d]生成图片信息失败' % (data['message_id'],), data['message_type'])
        except BaseException as e:
            warning('base exception in Choose Song: {}'.format(e))
            send(target, '[CQ:reply,id=%d]搜索失败' % (data['message_id'],), data['message_type'])
        return "OK"

    def get_plugin_info(self):
        return {
            'name': 'ChooseSong',
            'description': '点歌',
            'commandDescription': '点歌 [歌名]',
            'usePlace': ['group', 'private'],
            'showInHelp': True,
            'pluginConfigTableNames': [],
            'version': '1.0.0',
            'author': 'Unicorn',
        }
