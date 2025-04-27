from typing import Optional
from nonebot.internal.params import Depends

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent
from nonebot.exception import FinishedException
import feature_manager

# reference: https://github.com/bot-ssttkkl/nonebot-plugin-revoke/
def reply_message_id(event: MessageEvent) -> Optional[int]:
    message_id = None
    for seg in event.original_message:
        if seg.type == "reply":
            message_id = int(seg.data["id"])
            break
    return message_id

revoke = on_command("revoke", aliases={"撤回"}, priority=10, block=True)
@revoke.handle()
async def handle_function(bot: Bot, reply_msg_id: Optional[int] = Depends(reply_message_id)):
    if not feature_manager.get("revoke"):
        raise FinishedException
    if reply_msg_id is not None:
        await bot.delete_msg(message_id=reply_msg_id)
    raise FinishedException