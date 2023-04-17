import asyncio
import logging
import sys
from os import getenv
from datetime import datetime
from secrets import choice
from threading import Event

from pyrogram import Client, enums, filters
from pyrogram.errors import (
    ChatWriteForbidden,
    FloodWait,
    SlowmodeWait,
    UserBannedInChannel,
)
from pyrogram.raw.functions import Ping
from pyrogram.types import Message
from requests import get

list_chat = []

API_HASH = getenv("API_HASH")
API_ID = int(getenv("API_ID", ""))
STRING_SESSION = getenv("STRING_SESSION", "") # string session pyrogram

user = Client(
    name="user",
    api_id=API_ID,
    api_hash=API_HASH,
    in_memory=True,
    session_string=STRING_SESSION,
)

SPAM_COUNT = [0]


def increment_spam_count():
    SPAM_COUNT[0] += 1
    return spam_allowed()


def spam_allowed():
    return SPAM_COUNT[0] < 50


@user.on_message(filters.command("ping", ".") & filters.me)
async def pingme(client: Client, message: Message):
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    m_s = (end - start).microseconds / 1000
    await message.edit(f"**Pong!**\n`{m_s} ms`")


@user.on_message(filters.command("fetch", ".") & filters.me)
async def fetch_cmd(client: Client, message: Message):
    async for dialog in client.get_dialogs():
        if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            chat = dialog.chat.id
            if chat not in GCAST_BLACKLIST:
                list_chat.append(chat)
    await message.edit(f"Berhasil mengumpulkan list chat sebanyak {len(list_chat)}")


@user.on_message(filters.command(["clear", "delfetch"], ".") & filters.me)
async def clear_cmd(_, message: Message):
    list_chat.clear()
    await message.edit("List chat berhasil dihapus")


@user.on_message(filters.command(["listchat", "lc"], ".") & filters.me)
async def lchat(_, message: Message):
    if not list_chat:
        return await message.edit(
            "List chat kosong, Silahkan ketik `.fetch` terlebih dahulu"
        )
    text = "🔮 **List GCAST:** `Enabled`\n\n📚 **Daftar list Chat:**\n"
    text += f"**{list_chat}**\n"
    text += f"\n📝 **Total Chat:** `{len(list_chat)}`"
    await message.edit(text)


@user.on_message(filters.command(["broadcast", "gcast"], ".") & filters.me)
async def broadcast_cmd(client: Client, message: Message):
    text = (
        message.text.split(None, 1)[1]
        if len(
            message.command,
        )
        != 1
        else None
    )
    if message.reply_to_message:
        text = message.reply_to_message
    if not text:
        return await message.edit("**Berikan Sebuah Pesan atau Reply**")
    if not list_chat:
        return await message.edit(
            "List chat kosong, Silahkan ketik `.fetch` terlebih dahulu"
        )
    await message.edit("`Sedang mengirim pesan . . .`")
    while True:
        await asyncio.sleep(choice([90, 120, 180]))  # detik
        for chat in list_chat:
            try:
                if message.reply_to_message:
                    await text.copy(chat)
                    await asyncio.sleep(1)
                else:
                    await client.send_message(chat, text)
                    await asyncio.sleep(1)
            except ChatWriteForbidden:
                list_chat.remove(chat)
            except (FloodWait, SlowmodeWait) as e:
                flood_time = int(e.value)
                LOGS.info(f"Sleeping for {flood_time} seconds")
                await asyncio.sleep(flood_time)
                if message.reply_to_message:
                    await text.copy(chat)
                    await asyncio.sleep(1)
                else:
                    await client.send_message(chat, text)
                    await asyncio.sleep(1)
            except UserBannedInChannel:
                LOGS.error(
                    "Bot dimatikan\nKarena: akun terkena limit publik [ tidak bisa mengirim pesan di grup publik ]"
                )
                sys.exit()
            except BaseException as e:
                LOGS.error(e)


@user.on_message(filters.command(["dspam", "delayspam"], ".") & filters.me)
async def delayspam(client: Client, message: Message):
    delayspam = message.reply_to_message
    if not delayspam:
        await message.edit("**Reply ke pesan yang ingin di spam**")
        return
    delay = int(message.command[1])
    count = int(message.command[2])
    await message.delete()

    if not spam_allowed():
        return

    delaySpamEvent = Event()
    for i in range(0, count):
        if i != 0:
            delaySpamEvent.wait(delay)
        try:
            await delayspam.copy(message.chat.id)
        except FloodWait as e:
            LOGS.info(f"Sleeping for {e.value} seconds")
            await asyncio.sleep(e.value)
            await delayspam.copy(message.chat.id)
        except SlowmodeWait as e:
            LOGS.info(f"SlowmodeWait for {e.value} seconds")
            await asyncio.sleep(e.value)
            await delayspam.copy(message.chat.id)
        except UserBannedInChannel:
            LOGS.error(
                "Bot dimatikan\nKarena: akun terkena limit publik [ tidak bisa mengirim pesan di grup publik ]"
            )
            sys.exit()
        except BaseException as e:
            LOGS.info(e)
        limit = increment_spam_count()
        if not limit:
            break

    await client.send_message(
        "me", "**#DELAYSPAM**\nDelaySpam was executed successfully"
    )


logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
logging.getLogger("pyrogram").setLevel(logging.INFO)
logging.getLogger("pyrogram.session.internals.msg_id").setLevel(logging.WARNING)
LOGS = logging.getLogger(__name__)


while 0 < 6:
    _GCAST_BLACKLIST = get(
        "https://raw.githubusercontent.com/mrismanaziz/Reforestation/master/blacklistgcast.json"
    )
    if _GCAST_BLACKLIST.status_code != 200:
        if 0 != 5:
            continue
        GCAST_BLACKLIST = [-1001473548283, -1001390552926]
        break
    GCAST_BLACKLIST = _GCAST_BLACKLIST.json()
    break

del _GCAST_BLACKLIST


LOGS.info("Bot Berhasil diaktifkan")
user.run()
