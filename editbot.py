from mautrix.types import EventType
from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from typing import Type
from maubot.handlers import command



class Config(BaseProxyConfig):
  def do_update(self, helper: ConfigUpdateHelper) -> None:
    helper.copy("edit_room")
    helper.copy("ignorelist")

class EditBot(Plugin):

    async def start(self) -> None:
        self.config.load_and_update()
    
    def create_edit_message(self, author: str, room_id: str, new: str, original: str) -> str:
        result = ">  Message edited by %s in room %s\n\n" % (author, room_id)
        result += ">  Original message:\n%s\n\n" % original
        result += ">  New message:\n%s\n" % new
        result += "----------------------------------------\n\n"
        return result

    @event.on(EventType.ROOM_MESSAGE)
    async def edit_handler(self, event: MessageEvent) -> None:
        edit_message = event.content.get_edit()
        if edit_message == None:
            if event.content.body == "!editbot_disable":
                await self.editbot_disable(event)
            return
        if event.room_id in self.config["ignorelist"]:
            return
        # Get the message with id edit_message
        orig_event = await self.client.get_event(event.room_id, edit_message)
        if not isinstance(orig_event, MessageEvent):
            self.log.trace("Error: orig_event is not a MessageEvent: %s" % orig_event)
        
        # Write the message into the special room
        await self.client.send_notice(self.config["edit_room"], self.create_edit_message(event.sender, event.room_id, event.content.body, orig_event.content.body))


    async def editbot_disable(self, evt: MessageEvent) -> None: 
        room = evt.room_id
        self.log.info("Disabling editbot in room %s" % room)
        if room in self.config["ignorelist"]:
            self.log.info("Room %s already in ignorelist" % room)
            await evt.redact("Already disabled")
        else:
            self.config["ignorelist"].append(room)
            self.config.save()        
            await evt.redact("Disabled editbot in this room")
            self.log.info("Disabled editbot in room %s" % room)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
