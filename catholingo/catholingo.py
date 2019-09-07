#!/usr/bin/python3
#coding: utf8

import os
import discord
from sentence import Sentence, init as dbinit
from voice import Voice
import datetime

WEBHOOKS = dict()

class CathoLingo(discord.Client):
    COMMAND_PREFIX = "!"
    COMMENT_PREFIX = "-"

    def __init__(self, commands=None, patterns=None, on_message=None, on_edit=None, on_delete=None):
        super().__init__()
        self.commands = commands or dict()
        self.patterns = patterns or dict()
        self.on_message_parsers = on_message or list()
        self.on_edit_parsers = on_edit or list()
        self.on_delete_parsers = on_delete or list()

    async def on_ready(self):
        print('Now connected as {0.user.name}'.format(self))
        print('Ready. ')

    async def send_as(self, message, channel, ID):
        user = self.get_user(ID)
        try:
            if not user:
                user = await self.fetch_user(ID)
            URL = WEBHOOKS[channel.id]
        except:
            return await channel.send(message)
        webhook = discord.Webhook.from_url(URL, adapter=discord.RequestsWebhookAdapter())
        webhook.send(message, username=user.display_name + " (CathoLingo)", avatar_url=user.avatar_url)

    async def on_message(self, message):
        message.content = message.content.replace("<@!", "<@")
        if message.content.startswith(self.COMMENT_PREFIX):
            return
        elif message.content.startswith(self.COMMAND_PREFIX):
            return await self.command(message)
        await self.pattern(message)
        await self.on_message_parse(message)

    async def on_message_delete(self, message):
        await self.on_delete_parse(message)

    async def on_message_edit(self, before, after):
        await self.on_edit_parse(before, after)

    async def command(self, message):
        cmd, *args = message.content.split()
        for command, action in self.commands.items():
            if cmd == self.COMMAND_PREFIX+command:
                await action(self, message, *args)

    async def pattern(self, message):
        for pattern, action in self.patterns.items():
            if pattern in message.content:
                await action(self, message)

    async def on_message_parse(self, message):
        for parser in self.on_message_parsers:
            await parser(self, message)

    async def on_edit_parse(self, before, after):
        for parser in self.on_edit_parsers:
            await parser(self, before, after)

    async def on_delete_parse(self, message):
        for parser in self.on_delete_parsers:
            await parser(self, message)

async def say(catholingo, message, *args, **__):
    await message.channel.send(" ".join(args))

if __name__ == '__main__':
    print("Starting CathoLingo...")
    dbinit()
    print("Database initialized. ")
    for key, value in os.environ.items():
        if key.startswith("WEBHOOK_CHANNEL_"):
            try:
                WEBHOOKS[int(key.replace("WEBHOOK_CHANNEL_", ""))] = value
            except:
                pass
    print("{0} webhook(s) configured. ".format(len(WEBHOOKS)))
    voice = Voice()

    commands = {
        'join': voice.join,
        'quit': voice.quit,
        'pause': voice.pause,
        'resume': voice.resume,
        'stop': voice.stop,
        'tts': voice.on_tts,
        'say': say,
        'speak': Sentence.query,
        'speakfor': Sentence.speakfor,
        'speakfrom': Sentence.speakfrom,
        'startwith': Sentence.startwith,
        'endwith': Sentence.endwith,
    }
    patterns = {
        voice.YOUTUBE_PATTERN: voice.on_youtube,
    }
    on_message = [voice.on_catholingo, Sentence.save]
    on_edit = [Sentence.edit]
    on_delete = [Sentence.delete]

    print("Connection. ")
    CathoLingo(commands, patterns, on_message, on_edit, on_delete).run(os.environ.get('DISCORD_TOKEN'))
