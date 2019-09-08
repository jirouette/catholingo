#!/usr/bin/python3
#coding: utf8

import re
import discord
import youtube_dl
from gtts import gTTS

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Voice(object):
    YOUTUBE_PATTERN = "youtube.com/"

    def __init__(self):
        self.channel = None
        if not discord.opus.is_loaded():
            discord.opus.load_opus("libopus.so")

    async def join(self, catholingo, message, *_, **__):
        for channel in message.channel.guild.voice_channels:
            for member in channel.members:
                if member == message.author:
                    self.channel = await channel.connect()
                    return

    async def pause(self, *_, **__):
        if self.channel is None or not self.channel.is_connected():
            return
        self.channel.pause()

    async def resume(self, *_, **__):
        if self.channel is None or not self.channel.is_connected():
            return
        self.channel.resume()

    async def stop(self, *_, **__):
        if self.channel is None or not self.channel.is_connected():
            return
        self.channel.stop()

    async def quit(self, *_, **__):
        if self.channel is None or not self.channel.is_connected():
            return
        await self.channel.disconnect()

    async def tts(self, catholingo, text, lang="fr"):
        if self.channel is None or not self.channel.is_connected():
            return
        text = text.replace("@", "").lower()
        temp_file = "./tts.mp3"
        with open(temp_file, 'wb') as f:
            gTTS(text, lang=lang).write_to_fp(f)
        source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(temp_file))
        await self.stop()
        self.channel.play(source, after=lambda e: print('Player error: %s' % e) if e else None)

    async def on_youtube(self, catholingo, message):
        if self.channel is None or not self.channel.is_connected():
            return
        if self.YOUTUBE_PATTERN not in message.content:
            return
        URL = None
        for word in message.content.split():
            if self.YOUTUBE_PATTERN in word:
                URL = word
        if not URL:
            return
        player = await YTDLSource.from_url(URL, loop=catholingo.loop, stream=True)
        await self.stop()
        self.channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    async def on_catholingo(self, catholingo, message):
        if self.YOUTUBE_PATTERN in message.content:
            return
        if catholingo.user.name in message.author.name:
            await self.tts(catholingo, message.clean_content)

    async def on_tts(self, catholingo, message, *args, **__):
        msg = " ".join(message.clean_content.split()[1:])
        await self.tts(catholingo, msg)
