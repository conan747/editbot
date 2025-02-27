import pytest
from unittest.mock import AsyncMock, MagicMock
from maubot import MessageEvent

from editbot import EditBot, Config

CONFIG_DATA = {
    "edit_room": "!edit_room:example.com",
    "ignorelist": ["!ignored:example.com"]
}

@pytest.fixture
def mock_config():
    config = MagicMock(spec=Config)
    config.__getitem__.side_effect = lambda key: CONFIG_DATA[key]
    config.__setitem__.side_effect = lambda key, value: CONFIG_DATA.update({key: value})
    return config

@pytest.fixture
def plugin(mock_config):
    p = EditBot(client=AsyncMock(), loop=None, http=None, instance_id="test", log=MagicMock(), config=mock_config, database=None, webapp=None, webapp_url=None, loader=None)
    return p

@pytest.mark.asyncio
async def test_valid_edit_sends_notification(plugin):
    # Mock the edit event
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.room_id = "!test_room:example.com"
    mock_event.sender = "@user:example.com"
    
    # Create edit content mock
    edit_content = MagicMock()
    edit_content.get_edit.return_value = "$original_event_id"
    mock_event.content = edit_content
    mock_event.content.body = "edited message content"

    # Create fake original event
    orig_event = MagicMock(spec=MessageEvent)
    orig_event.content = MagicMock()
    orig_event.content.body = "original message content"

    # Mock client methods
    plugin.client.get_event = AsyncMock(return_value=orig_event)
    plugin.client.send_notice = AsyncMock()

    # Trigger the handler
    await plugin.edit_handler(mock_event)

    # Verify original message was fetched
    plugin.client.get_event.assert_awaited_once_with(
        "!test_room:example.com",
        "$original_event_id"
    )

    # Verify notification was sent
    expected_message = (
        ">  Message edited by @user:example.com in room !test_room:example.com\n\n"
        ">  Original message:\noriginal message content\n\n"
        ">  New message:\nedited message content\n"
        "----------------------------------------\n\n"
    )
    plugin.client.send_notice.assert_awaited_once_with(
        "!edit_room:example.com",
        expected_message
    )

@pytest.mark.asyncio
async def test_message_not_sent_when_room_ignored(plugin):
    # Set up event from ignored room
    mock_event = MagicMock(spec=MessageEvent)
    mock_event.room_id = "!ignored:example.com"
    mock_event.sender = "@user:example.com"
    
    # Create valid edit content
    edit_content = MagicMock()
    edit_content.get_edit.return_value = "$dummy_event_id"
    mock_event.content = edit_content

    # Trigger the handler
    await plugin.edit_handler(mock_event)

    # Ensure no messages were sent
    plugin.client.send_notice.assert_not_called()

@pytest.mark.asyncio
async def test_editbot_disable(plugin):
    # Set up event from ignored room
    mock_event = AsyncMock(spec=MessageEvent)
    mock_event.room_id = "!new:example.com"
    mock_event.sender = "@user:example.com"
    mock_event.redact = AsyncMock()
    # mock_event.client = AsyncMock()
    edit_content = MagicMock()
    edit_content.get_edit.return_value = None
    edit_content.body = "!editbot_disable"
    mock_event.content = edit_content
    
    # Trigger the handler
    await plugin.edit_handler(mock_event)

    # Ensure config was saved
    plugin.config.save.assert_called_once()

    assert("!new:example.com" in plugin.config["ignorelist"])

    # Ensure reaction was sent
    mock_event.redact.assert_called_once_with("Disabled editbot in this room")


@pytest.mark.asyncio
async def test_editbot_already_disabled(plugin):
    # Set up event from ignored room
    mock_event = AsyncMock(spec=MessageEvent)
    mock_event.room_id = "!ignored:example.com"
    mock_event.sender = "@user:example.com"
    mock_event.redact = AsyncMock()
    # mock_event.client = AsyncMock()
    edit_content = MagicMock()
    edit_content.get_edit.return_value = None
    edit_content.body = "!editbot_disable"
    mock_event.content = edit_content
    
    # Trigger the handler
    await plugin.edit_handler(mock_event)

    # Ensure config was saved
    plugin.config.save.assert_not_called()

    # Ensure reaction was sent
    mock_event.redact.assert_called_once_with("Already disabled")