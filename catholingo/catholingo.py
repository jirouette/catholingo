#!/usr/bin/python3
#coding: utf8

import os
import discord
from voice import Voice

class CathoLingo(discord.Client):
    COMMAND_PREFIX = "!"
    COMMENT_PREFIX = "-"

    def __init__(self, commands=None, patterns=None, parsers=None):
        super().__init__()
        self.commands = commands or dict()
        self.patterns = patterns or dict()
        self.parsers = parsers or list()

    async def get_user_by_id(self, ID):
        ID = int(ID)
        user = self.get_user(ID)
        if not user:
            user = await self.fetch_user(ID)
        return user

    async def on_ready(self):
        print('Now connected as{0.user.name} ! '.format(self))
        print('Ready. ')

    async def on_message(self, message):
        if message.content.startswith(self.COMMENT_PREFIX):
            return
        elif message.content.startswith(self.COMMAND_PREFIX):
            return await self.command(message)
        await self.pattern(message)
        await self.parse(message)

    async def command(self, message):
        cmd, *args = message.content.split()
        for command, action in self.commands.items():
            if cmd == self.COMMAND_PREFIX+command:
                await action(self, message, *args)

    async def pattern(self, message):
        for pattern, action in self.patterns.items():
            if pattern in message.content:
                await action(self, message)

    async def parse(self, message):
        for parser in self.parsers:
            await parser(self, message)


async def say(catholingo, message, *args, **__):
    await message.channel.send(" ".join(args))

if __name__ == '__main__':
    print("Starting CathoLingo...")
    voice = Voice()

    commands = {
        'join': voice.join,
        'quit': voice.quit,
        'pause': voice.pause,
        'resume': voice.resume,
        'stop': voice.stop,
        'tts': voice.on_tts,
        'say': say
    }
    patterns = {
        voice.YOUTUBE_PATTERN: voice.on_youtube,
    }
    parsers = [voice.on_catholingo]

    CathoLingo(commands, patterns, parsers).run(os.environ.get('DISCORD_TOKEN'))