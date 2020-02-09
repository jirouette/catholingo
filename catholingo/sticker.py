#!/usr/bin/python3
#coding: utf8

import discord
import shutil
import os

STICKER_DIRECTORY = os.environ.get("STICKER_DIRECTORY", "/var/stickers")

class Sticker(object):
    @staticmethod
    def clean_sticker_name(sticker_name):
        return sticker_name.replace('..', '').replace('/', '').replace('\\', '')

    @classmethod
    async def add_sticker(cls, catholingo, message, *arg, **__):
        if len(arg) < 1 or len(message.attachments) < 1:
            return
        sticker = cls.clean_sticker_name(arg[0])
        userID = str(message.author.id)
        path = STICKER_DIRECTORY+"/"+userID
        if not os.path.isdir(path):
            os.mkdir(path)
        path += "/"+sticker
        if os.path.isdir(path):
            await message.channel.send("Already existing 😔")
            return
        os.mkdir(path)
        file = message.attachments[0]
        await file.save(open(path+"/"+file.filename, "wb"))
        await message.channel.send("👌")

    @classmethod
    async def sticker(cls, catholingo, message, *arg, **__):
        if len(arg) < 1:
            return
        sticker = cls.clean_sticker_name(arg[0])
        userID = str(message.author.id)
        path = STICKER_DIRECTORY+"/"+userID+"/"+sticker
        if not os.path.isdir(path):
            await message.channel.send("Unknown sticker 😔")
            return
        try:
            filename = os.listdir(path)[0]
        except:
            await message.channel.send("File not found 😔")
            return
        await catholingo.send_as('', message.channel, message.author.id, file=discord.File(path+"/"+filename))
        try:
            await message.delete()
        except:
            pass

    @classmethod
    async def list_stickers(cls, catholingo, message, *arg, **__):
        userID = str(message.author.id)
        path = STICKER_DIRECTORY+"/"+userID
        stickers = sorted(os.listdir(path))
        if len(stickers) == 0:
            await message.channel.send("No sticker found 😔")
            return
        await message.channel.send('`'+'` `'.join(stickers)+'`')

    @classmethod
    async def remove_sticker(cls, catholingo, message, *arg, **__):
        if len(arg) < 1:
            return
        sticker = cls.clean_sticker_name(arg[0])
        userID = str(message.author.id)
        path = STICKER_DIRECTORY+"/"+userID+"/"+sticker
        if not os.path.isdir(path):
            await message.channel.send("Unknown sticker 😔")
            return
        try:
            shutil.rmtree(path)
        except:
            await message.channel.send("Could not remove sticker 😔")
            return
        await message.channel.send("👌")
