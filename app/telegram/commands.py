from aiogram import types

COMMANDS_TG = [
    types.BotCommand(command="start", description="Start bot"),
    types.BotCommand(command="commands", description="Commands list"),
    types.BotCommand(command="stop", description="Stop bot"),
]

COMMANDS_BOT = [
    {"description": "Anime actions", "command": "/anime"},
    {
        "description": "Admin:",
        "subcommands": [
            {"description": "Reload secrets", "command": "/secrets_reload"}
        ],
    },
]
