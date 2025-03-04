# Edit Bot

This is a [maubot](https://github.com/maubot/maubot) to record message edits.

You can disable rooms that will be watched by adding them to the configuration or using the magic word `!editbot_disable` on the room. You can also react with "🔇" to a message in the edit_room in order to disable the plugin for the room.

## Rationale

I'm always curious what people wrote and then rephrased so I keep a log of the diffs.

Unfortunately it won't work for deleted messages since these are deleted on the server.