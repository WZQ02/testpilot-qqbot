from nonebot import on_notice
from nonebot.adapters.onebot.v11 import NoticeEvent, PokeNotifyEvent, Message
import random, math
from nonebot.exception import FinishedException
import feature_manager
import path_manager

pokeresp = on_notice()

@pokeresp.handle()
async def handle_function(event: NoticeEvent):
    if not feature_manager.get("poke"):
        raise FinishedException
    if isinstance(event, PokeNotifyEvent):
        if event.target_id == event.self_id:
            # group_id = event.group_id
            # user_id = event.user_id
            rd = math.ceil(random.random()*(11+4*2))
            msg = ""
            if rd <= 10:
                msg = Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/poke/poke_'+str(rd)+'.jpg,sub_type=1]')
            elif rd == 11:
                msg = Message('[CQ:image,file=file:///'+path_manager.bf_path()+'images/poke/poke_11.gif,sub_type=1]')
            elif 11 < rd < 14:
                msg = "干嘛！"
            elif 13 < rd < 16:
                msg = "不可以戳我哟！"
            elif 15 < rd < 18:
                msg = "诶呦！"
            elif 17 < rd < 20:
                msg = "喵"
            await pokeresp.finish(msg)