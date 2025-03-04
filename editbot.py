from mautrix.types import EventType, RelationType
from maubot import Plugin, MessageEvent
from maubot.handlers import event
from mautrix.util.config import BaseProxyConfig, ConfigUpdateHelper
from typing import Type
import re

SILENCE_REACTION = "🔇"
ROOM_ID_REGEX = re.compile(r".*room_id: '([^']*)'")

class Config(BaseProxyConfig):
  def do_update(self, helper: ConfigUpdateHelper) -> None:
    helper.copy("edit_room")
    helper.copy("ignorelist")

class EditBot(Plugin):

    async def start(self) -> None:
        self.config.load_and_update()
    
    def create_edit_message(self, author: str, room_id: str, new: str, original: str, sender_name: str, room_name: str|None) -> str:
        result = ">  Message edited by %s (%s) in " % (sender_name, author)
        if room_name:
            result += "room %s. " % (room_name)
        result += "room_id: '%s'\n\n" % room_id
        result += ">  Original message:\n%s\n\n" % original
        result += ">  New message:\n%s\n" % new
        result += "----------------------------------------\n\n"
        return result

    @event.on(EventType.ALL)
    async def edit_handler(self, event: MessageEvent) -> None:
        if event.type not in [EventType.ROOM_MESSAGE, EventType.REACTION]:
            self.log.debug("Ignoring event type %s", event.type)
            return
        if event.type == EventType.REACTION and event.room_id == self.config["edit_room"]:
            relates_to = event.content.relates_to
            if relates_to == None or relates_to.rel_type is not RelationType.ANNOTATION or relates_to.key != SILENCE_REACTION:
                self.log.debug("Wrong reaction: %s" % event.content)
                return
            event_to_silence: MessageEvent = await self.client.get_event(self.config["edit_room"], relates_to.event_id)
            text = event_to_silence.content.body
            matches = ROOM_ID_REGEX.match(text)
            if matches:
                room_id = matches.group(1)
                await self.editbot_disable(room_id)
            else:
                self.log.warning(f"Could not match room id from message in: {text}")
            return
        edit_message = event.content.get_edit()
        if edit_message == None:
            if event.content.body == "!editbot_disable":
                await self.editbot_disable(event.room_id, event)
            return

        if event.room_id in self.config["ignorelist"]:
            return
        # Get the message with id edit_message
        orig_event = await self.client.get_event(event.room_id, edit_message)
        if not isinstance(orig_event, MessageEvent):
            self.log.trace("Error: orig_event is not a MessageEvent: %s" % orig_event)
        
        sender_profile = await self.client.get_profile(event.sender)
        sender_name = sender_profile.displayname
        room_state = await self.client.get_state_event(event.room_id, EventType.ROOM_NAME)
        room_name = room_state.name

        # Write the message into the special room
        await self.client.send_notice(self.config["edit_room"], self.create_edit_message(event.sender, event.room_id, event.content.body, orig_event.content.body, sender_name, room_name))


    async def editbot_disable(self, room: str, evt: MessageEvent|None = None) -> None: 
        self.log.info("Disabling editbot in room %s" % room)
        if room in self.config["ignorelist"]:
            self.log.info("Room %s already in ignorelist" % room)
            if evt:
                await evt.redact("Already disabled")
        else:
            self.config["ignorelist"].append(room)
            self.config.save()
            if evt:
                await evt.redact("Disabled editbot in this room")
            self.log.info("Disabled editbot in room %s" % room)

    @classmethod
    def get_config_class(cls) -> Type[BaseProxyConfig]:
        return Config
