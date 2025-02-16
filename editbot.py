from mautrix.types import EventType
from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from typing import Type



class Config(BaseProxyConfig):
  def do_update(self, helper: ConfigUpdateHelper) -> None:
    helper.copy("edit_room")
    helper.copy("ignorelist")

class EditBot(Plugin):

    EDIT_ROOM_ID = "!FPsmGPDLcDywraUQGb:one.ems.host"


    async def start(self) -> None:
        self.config.load_and_update()
    
    def create_edit_message(self, author: str, room_id: str, new: str, original: str) -> str:
        result = ">  Message edited by %s in room %s\n\n" % (author, room_id)
        result += ">  Original message:\n%s\n\n" % original
        result += ">  New message:\n%s" % new
        result += "----------------------------------------\n"
        return result

    # def create_delete_message(self, author: str, room_id: str, original: str) -> str:
    #     result = ">  Message deleted by %s in room %s\n\n" % (author, room_id)
    #     result += ">  Original message:\n%s" % original
    #     result += "----------------------------------------\n"
    #     return result


    # @event.on(EventType.ROOM_REDACTION)
    # async def delete_handler(self, event: MessageEvent) -> None:
    #     # Get the message with id edit_message
    #     orig_event_id = event.content.get("redacts")
    #     if orig_event_id == None:
    #         self.log.debug("No redacts key in redaction event: %s" % event.content)
    #         return
    #     orig_event = await self.client.get_event(event.room_id, orig_event_id)
    #     if not isinstance(orig_event, MessageEvent):
    #         self.log.trace("Error: orig_event is not a MessageEvent: %s" % orig_event)
        
    #     # Write the message into the special room
    #     await self.client.send_notice(self.EDIT_ROOM_ID, self.create_delete_message(event.sender, event.room_id, orig_event.content.body))


    @event.on(EventType.ROOM_MESSAGE)
    async def edit_handler(self, event: MessageEvent) -> None:
        edit_message = event.content.get_edit()
        if edit_message == None:
            return
        if event.room_id in self.config["ignorelist"]:
            return
        # Get the message with id edit_message
        orig_event = await self.client.get_event(event.room_id, edit_message)
        if not isinstance(orig_event, MessageEvent):
            self.log.trace("Error: orig_event is not a MessageEvent: %s" % orig_event)
        
        # Write the message into the special room
        await self.client.send_notice(self.config["edit_room"], self.create_edit_message(event.sender, event.room_id, event.content.body, orig_event.content.body))


    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
