from typing import Any, Union
from .bot_protocol_base import parse_protocol_head, BotProtocolType, BotProtocolBase, protocol_classification
from utils.standard_plugin import StandardPlugin, CronStandardPlugin
from utils.sql_utils import new_sql_session
from utils.basic_event import send, warning
from utils.basic_configs import BOT_SELF_QQ

class BotProtocolStatusQuery(BotProtocolBase):
    """状态查询协议
    #L0: LUB_NET_PROTOCOL ${PROTOCOL_VERSION}
    #L1: STATUS QUERY
    #L2: ${UUID}
    #L3: ${TARGET_QQ}
    """
    def __init__(self, uuid:str, targetId:int):
        self.uuid = uuid
        self.targetId = targetId
    def get_type(self) -> BotProtocolType:
        return BotProtocolType.STATUS_QUERY
    def to_str(self) -> str:
        return (
            'LUB_NET_PROTOCOL 000001\n'
            'STATUS QUERY\n'
            f'{self.uuid}\n'
            f'{self.targetId}'
        )
    @staticmethod
    def from_str(text:str)-> "BotProtocolStatusQuery":
        texts = text.strip().split('\n')
        if len(texts) != 4:
            raise ValueError('len(lines) != 4')
        succ, reason = parse_protocol_head(texts[0])
        if not succ:
            raise ValueError('Head Parse Error: {}'.format(reason))
        uuid = texts[2].strip()
        targetId = texts[3].strip()
        if not targetId.isdigit():
            raise ValueError('target id is not digit')
        return BotProtocolStatusQuery(uuid=uuid, targetId=targetId)

class BotProtocolStatusReply(BotProtocolBase):
    """状态应答协议
    #L0: LUB_NET_PROTOCOL ${PROTOCOL_VERSION}
    #L1: STATUS REPLY
    #L2: ${QUERY_UUID}
    """
    def __init__(self, uuid:str):
        self.uuid = uuid
    def get_type(self) -> BotProtocolType:
        return BotProtocolType.STATUS_REPLY
    def to_str(self) -> str:
        return (
            'LUB_NET_PROTOCOL 000001\n'
            'STATUS REPLY\n'
            f'{self.uuid}'
        )
    @staticmethod
    def from_str(text:str)-> "BotProtocolStatusReply":
        texts = text.strip().split('\n')
        if len(texts) != 3:
            raise ValueError('len(lines) != 3')
        succ, reason = parse_protocol_head(texts[0])
        if not succ:
            raise ValueError('Head Parse Error: {}'.format(reason))
        uuid = texts[2].strip()
        return BotProtocolStatusReply(uuid=uuid)

def createStatusSql():
    mydb, mycursor = new_sql_session()
    mycursor.execute("""create table if not exists `botStatusMonitor`(
        `network_group` bigint unsigned not null,
        `target_id` bigint not null,
        primary key(`network_group`, `target_id`)
    )""")

class BotStatusMonitor(StandardPlugin, CronStandardPlugin):
    initGuard = True
    def __init__(self) -> None:
        if self.initGuard:
            self.initGuard = False
            createStatusSql()
            self.start()
    def tick(self) -> None:
        pass
    def judge_trigger(self, msg: str, data: Any) -> bool:
        protocolType = protocol_classification(msg)
        return protocolType == BotProtocolType.STATUS_REPLY
    def execute_event(self, msg: str, data: Any) -> Union[str, None]:
        groupId = data['group_id']
        try:
            reply = BotProtocolStatusReply.from_str(msg)
        except ValueError as e:
            print(e)
            return 'OK'

        return 'OK'
    def get_plugin_info(self, )->Any:
        return {
            'name': 'BotStatusMonitor',
            'description': '机器人组网 - 状态监控',
            'commandDescription': '--',
            'usePlace': ['group', ],
            'showInHelp': False,
            'pluginConfigTableNames': ['botStatusMonitor'],
            'version': '1.0.0',
            'author': 'Unicorn',
        }

class BotStatusReply(StandardPlugin):
    def judge_trigger(self, msg: str, data: Any) -> bool:
        protocolType = protocol_classification(msg)
        return protocolType == BotProtocolType.STATUS_QUERY
    def execute_event(self, msg: str, data: Any) -> Union[str, None]:
        groupId = data['group_id']
        try:
            query = BotProtocolStatusQuery.from_str(msg)
        except ValueError as e:
            print(e)
            return 'OK'
        if query.targetId != BOT_SELF_QQ: return 'OK'
        reply = BotProtocolStatusReply(query.uuid)
        send(groupId, reply.to_str())
        return "OK"
    def get_plugin_info(self, )->Any:
        return {
            'name': 'BotStatusReply',
            'description': '机器人组网 - 状态回应',
            'commandDescription': '--',
            'usePlace': ['group', ],
            'showInHelp': False,
            'pluginConfigTableNames': [],
            'version': '1.0.0',
            'author': 'Unicorn',
        }