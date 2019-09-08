#!/usr/bin/python3
#coding: utf8

from peewee import (MySQLDatabase, Model, CharField, ForeignKeyField, TextField, BigIntegerField,
                    DateTimeField, BooleanField, IntegerField, fn)
from playhouse.db_url import connect as connect_url
import datetime
import os

db = MySQLDatabase(
    os.environ.get('DATABASE', 'catholingo'),
    user=os.environ.get('DB_USER', 'catholingo'),
    password=os.environ.get('DB_PASSWORD', ''),
    host=os.environ.get('DB_HOST', 'mysql'),
    charset='utf8mb4')

class Word(Model):
    class Meta:
        database = db

    message_id = BigIntegerField()
    author_id = BigIntegerField()
    channel_id = BigIntegerField()
    guild_id = BigIntegerField()
    datetime = DateTimeField(default=datetime.datetime.now)
    author_username = CharField(max_length=50)
    author_display_name = CharField(max_length=50)
    previous_previous_word = CharField(null=True, max_length=500)
    previous_word = CharField(null=True, max_length=500)
    word = CharField(max_length=500)
    next_word = CharField(null=True, max_length=500)
    next_next_word = CharField(null=True, max_length=500)
    is_nsfw = BooleanField(null=False, default=False)

def init():
    create_tables()

def none_or(field, val):
    return field == val if not (val is None) else field >> None

def execute(sql):
    return db.execute_sql(sql)

def random():
    return fn.Rand() if type(db) is MySQLDatabase else fn.Random()

def connect():
    if db.is_closed():
        db.connect()

def close():
    if not db.is_closed():
        db.close()

def transaction():
    return db.transaction()

def create_tables():
    connect()
    with transaction():
        db.create_tables([Word], safe=True)

class connection(object):
    def __enter__(self):
        connect()
    def __exit__(self, type, value, traceback):
        close()

class Sentence(object):
    @classmethod
    async def save(cls, catholingo, message, no_save=False):
        if not message.content:
            return []
        if message.content[0:2] not in ["!w", "!m"] and message.content[0] in [catholingo.COMMAND_PREFIX, catholingo.COMMENT_PREFIX]:
            return []
        if catholingo.user.name in message.author.name or "Jewvenden" in message.author.name:
            return []

        if catholingo.user in message.mentions or catholingo.user.name.lower() in message.content.lower():
            await cls.query(catholingo, message)

        text = message.content.split()
        entries = []
        for i, word in enumerate(text):
            entry = dict(
                message_id=message.id,
                author_id=message.author.id,
                channel_id=message.channel.id,
                guild_id=message.channel.guild.id if hasattr(message.channel, "guild") else 0,
                datetime=message.created_at,
                author_username=message.author.name,
                author_display_name=message.author.display_name,
                previous_previous_word=text[i-2][:500] if i > 1 else None,
                previous_word=text[i-1][:500] if i > 0 else None,
                word=word[:500],
                next_word=text[i+1][:500] if i < len(text)-1 else None,
                next_next_word=text[i+2][:500] if i < len(text)-2 else None,
                is_nsfw=message.channel.is_nsfw())
            entries.append(entry)
        if not no_save:
            Word.insert_many(entries).execute()
        return entries

    @classmethod
    async def edit(cls, catholingo, before, after):
        await cls.delete(catholingo, before)
        await cls.save(catholingo, after)

    @classmethod
    async def delete(cls, catholingo, message):
        Word.delete().where(Word.message_id == message.id).execute()

    @staticmethod
    def generator(conditions=None, ordered_conditions=None, maxlength=100):
        if type(ordered_conditions) is not list:
            ordered_conditions = [ordered_conditions] if ordered_conditions else []
        pos = 0
        payload = []
        previous_previous_word = None
        previous_word = None
        word = True
        with connection():
            while word:
                _cond = none_or(Word.previous_previous_word, previous_previous_word)
                _cond = _cond & none_or(Word.previous_word, previous_word)
                if conditions is not None:
                    _cond = _cond & conditions
                try:
                    _cond = _cond & ordered_conditions[pos]
                except IndexError:
                    pass
                pos += 1
                word = Word.select().where(_cond).order_by(random()).first()
                if word:
                    payload.append(word.word)
                    previous_previous_word = previous_word
                    previous_word = word.word
                    if word.next_word is None:
                        break
        return " ".join(payload) or "No result"

    @staticmethod
    def reverse_generator(conditions=None, ordered_conditions=None, maxlength=100):
        if type(ordered_conditions) is not list:
            ordered_conditions = [ordered_conditions] if ordered_conditions else []
        pos = 0
        payload = []
        next_next_word = None
        next_word = None
        word = True
        with connection():
            while word:
                _cond = none_or(Word.next_next_word, next_next_word)
                _cond = _cond & none_or(Word.next_word, next_word)
                if conditions is not None:
                    _cond = _cond & conditions
                try:
                    _cond = _cond & ordered_conditions[pos]
                except IndexError:
                    pass
                pos += 1
                word = Word.select().where(_cond).order_by(random()).first()
                if word:
                    payload.append(word.word)
                    next_next_word = next_word
                    next_word = word.word
                    if word.previous_word is None:
                        break
        payload.reverse()
        return " ".join(payload) or "No result"

    @classmethod
    async def query(cls, catholingo, message, *_, **__):
        await message.channel.trigger_typing()
        conditions = True
        if not message.channel.is_nsfw():
            conditions = Word.is_nsfw == False
        await message.channel.send(cls.generator(conditions))

    @classmethod
    async def speakfor(cls, catholingo, message, *arg, **__):
        if len(arg) < 1:
            return
        await message.channel.trigger_typing()
        ID = 0
        conditions = True
        if not message.channel.is_nsfw():
            conditions = Word.is_nsfw == False
        try:
            ID = int(arg[0].replace('<@', '').replace('!', '').replace('>', ''))
            conditions = (Word.author_id == ID) & conditions
        except:
            username = " ".join(arg)
            conditions = ((Word.author_username == username) | (Word.author_display_name == username)) & conditions
        payload = cls.generator(conditions)
        if payload == "No result":
            return await message.channel.send(payload)
        await catholingo.send_as(payload, message.channel, ID)

    @classmethod
    async def speakfrom(cls, catholingo, message, *arg, **__):
        if len(arg) < 1:
            return
        await message.channel.trigger_typing()
        conditions = True
        if not message.channel.is_nsfw():
            conditions = Word.is_nsfw == False
        try:
            ID = int(arg[0].replace('<#', '').replace('!', '').replace('>', ''))
        except:
            return
        await message.channel.send(cls.generator((Word.channel_id == ID) & conditions))

    @classmethod
    async def startwith(cls, catholingo, message, *arg, **__):
        await message.channel.trigger_typing()
        conditions = True
        if not message.channel.is_nsfw():
            conditions = Word.is_nsfw == False
        payload = cls.generator(conditions, ordered_conditions=[Word.word == word for word in arg])
        await message.channel.send(payload)

    @classmethod
    async def endwith(cls, catholingo, message, *arg, **__):
        await message.channel.trigger_typing()
        conditions = True
        if not message.channel.is_nsfw():
            conditions = Word.is_nsfw == False
        payload = cls.reverse_generator(conditions, ordered_conditions=[Word.word == word for word in arg][::-1])
        await message.channel.send(payload)

    @classmethod
    async def sync(cls, catholingo, message, *_, **__):
        finished = False
        channel = message.channel
        previous_message = None
        Word.delete().where(Word.channel_id == channel.id).execute()
        while not finished:
            finished = True
            entries = []
            async for message in channel.history(after=previous_message, oldest_first=True):
                entries += await cls.save(catholingo, message, no_save=True)
                previous_message = message
                finished = False
            Word.insert_many(entries).execute()
        await message.channel.send("Finished ! :3")
