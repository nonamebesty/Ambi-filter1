import os
import logging
import random
import asyncio
import pytz
from Script import script
from datetime import datetime
from database.refer import referdb
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup , ForceReply, ReplyKeyboardMarkup
from pyrogram.types import *
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id, get_bad_files
from database.users_chats_db import db
from database.trending import Jisshu_TOP
from database.config_db import mdb
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, DATABASE_URI, REFER_PICS, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT, CHNL_LNK, GRP_LNK, REQST_CHANNEL, SUPPORT_CHAT_ID, SUPPORT_CHAT, MAX_B_TN, VERIFY, SHORTLINK_API, SHORTLINK_URL, TUTORIAL, IS_TUTORIAL, PREMIUM_USER, PICS, SUBSCRIPTION
from utils import get_settings, get_size, is_req_subscribed, save_group_settings, temp, verify_user, check_token, check_verification, get_token, get_shortlink, get_tutorial
from database.connections_mdb import active_connection
#from plugins.pm_filter import ENABLE_SHORTLINK
import re, asyncio, os, sys
import json
import base64
logger = logging.getLogger(__name__)
# https://t.me/JISSHU_BOTS
# https://t.me/Jisshu_support
TIMEZONE = "Asia/Kolkata"
BATCH_FILES = {}

EMOJIS = [ "👀", "😱", "🔥", "😍", "🎉", "🥰", "😇", "⚡" ]


movie_series_db = Jisshu_TOP(DATABASE_URI)


@Client.on_callback_query(filters.regex("mostsearch"))
async def topsearch_callback(client, callback_query):
    
    def is_alphanumeric(string):
        return bool(re.match('^[a-zA-Z0-9 ]*$', string))
    
    limit = 20  # Default limit or get from somewhere else if needed

    top_messages = await mdb.get_top_messages(limit)

    # Use a set to ensure unique messages (case insensitive).
    seen_messages = set()
    truncated_messages = []

    for msg in top_messages:
        # Convert message to lower case for uniqueness check
        msg_lower = msg.lower()
        if msg_lower not in seen_messages and is_alphanumeric(msg):
            seen_messages.add(msg_lower)
            
            if len(msg) > 35:
                truncated_messages.append(msg[:32] + "...")
            else:
                truncated_messages.append(msg)

    # Create keyboard layout with 2 messages per row
    keyboard = [truncated_messages[i:i+2] for i in range(0, len(truncated_messages), 2)]
    
    reply_markup = ReplyKeyboardMarkup(
        keyboard, 
        one_time_keyboard=True, 
        resize_keyboard=True, 
        placeholder="Most searches of the day"
    )
    
    await callback_query.message.reply_text("<b>Hᴇʀᴇ Iꜱ Tʜᴇ Mᴏꜱᴛ Sᴇᴀʀᴄʜᴇꜱ Lɪꜱᴛ 👇</b>", reply_markup=reply_markup)
    await callback_query.answer()
    
@Client.on_callback_query(filters.regex(r"^trending$"))
async def suggestion_click_2(client, query):
    # Get movie and series names from the database for the second suggestion
    movie_series_names = await movie_series_db.get_movie_series_names(1)
    
    # Check if there are any names in the database
    if not movie_series_names:
        await query.message.reply("Tʜᴇʀᴇ Aʀᴇ Nᴏ ᴍᴏᴠɪᴇ Oʀ Sᴇʀɪᴇs Nᴀᴍᴇs Aᴠᴀɪʟᴀʙʟᴇ Fᴏʀ Tʜᴇ Tᴏᴘ Sᴇᴀʀᴄʜᴇs.")
        return

    # Create rows of buttons, with each row containing two buttons
    buttons = [movie_series_names[i:i + 2] for i in range(0, len(movie_series_names), 2)]

    # Create a ReplyKeyboardMarkup with buttons arranged in a grid layout
    spika = ReplyKeyboardMarkup(
        buttons,
        resize_keyboard=True
    )

    # Reply to the user with the keyboard
    await query.message.reply("<b>Here Is The Top Trending List 👇</b>", reply_markup=spika)

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    await message.react(emoji=random.choice(EMOJIS), big=True)
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [[
                    InlineKeyboardButton('☆ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ☆', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('🍁 Hᴏᴡ Tᴏ Uꜱᴇ 🍁', url="https://t.me/HeartThieft_bot?start=help")
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.GSTART_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup, disable_web_page_preview=True)
        await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
        if not await db.get_chat(message.chat.id):
            total=await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
            await db.add_chat(message.chat.id, message.chat.title)
        return 
        
    if len(message.command) == 2 and message.command[1].startswith("reff_"):
        try:
            user_id = int(message.command[1].split("_")[1])
        except ValueError:
            await message.reply_text("Iɴᴠᴀʟɪᴅ ʀᴇғᴇʀ⁉️")
            return
        if user_id == message.from_user.id:
            await message.reply_text("Hᴇʏ ᴅᴜᴅᴇ, ʏᴏᴜ ᴄᴀɴ ɴᴏᴛ ʀᴇғᴇʀ ʏᴏᴜʀsᴇʟғ⁉️")
            return
        if referdb.is_user_in_list(message.from_user.id):
            await message.reply_text("‼️ Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ᴏʀ ᴊᴏɪɴᴇᴅ")
            return
        if await db.is_user_exist(message.from_user.id): 
            await message.reply_text("‼️ Yᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ᴀʟʀᴇᴀᴅʏ ɪɴᴠɪᴛᴇᴅ ᴏʀ ᴊᴏɪɴᴇᴅ")
            return            
        try:
            uss = await client.get_users(user_id)
        except Exception:
            return
        referdb.add_user(message.from_user.id)
        fromuse = referdb.get_refer_points(user_id) + 10
        if fromuse == 100:
            referdb.add_refer_points(user_id, 0) 
            await message.reply_text(f"𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙞𝙣𝙫𝙞𝙩𝙚𝙙 𝙗𝙮 {uss.mention}!") 
            await client.send_message(user_id, text=f"𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙞𝙣𝙫𝙞𝙩𝙚𝙙 𝙗𝙮 {message.from_user.mention}!") 
            await add_premium(client, user_id, uss)
        else:
            referdb.add_refer_points(user_id, fromuse)
            await message.reply_text(f"𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙗𝙚𝙚𝙣 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙞𝙣𝙫𝙞𝙩𝙚𝙙 𝙗𝙮 {uss.mention}!")
            await client.send_message(user_id, f"𝙔𝙤𝙪 𝙝𝙖𝙫𝙚 𝙨𝙪𝙘𝙘𝙚𝙨𝙨𝙛𝙪𝙡𝙡𝙮 𝙞𝙣𝙫𝙞𝙩𝙚𝙙 {message.from_user.mention}!")
        return
        
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
                    InlineKeyboardButton('☆ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ☆', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('Hᴇʟᴘ ⚙️', callback_data='help'),
                    InlineKeyboardButton('Aʙᴏᴜᴛ ✌️', callback_data='about')
                ],[
                    InlineKeyboardButton('Pʀᴇᴍɪᴜᴍ 💳', callback_data="premium_info"),
                    InlineKeyboardButton('Rᴇғᴇʀ ⚜️', callback_data="reffff")
                ],[
                    InlineKeyboardButton('♨️ Gʀᴏᴜᴘ Rᴜʟᴇꜱ ♨️', callback_data="rlu"),
                    InlineKeyboardButton('♻️ Exᴛʀᴀ Fᴇᴀᴛᴜʀᴇꜱ ✅', callback_data='extra')
                ],[
                    InlineKeyboardButton('✇ Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ ✇', callback_data='JoinUᴘᴅᴀᴛᴇs')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "Gᴏᴏᴅ Mᴏʀɴɪɴɢ 🌞" 
        elif curr_time < 17:
            gtxt = "Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ 🌗" 
        elif curr_time < 21:
            gtxt = "Gᴏᴏᴅ Eᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "Gᴏᴏᴅ Nɪɢʜᴛ 🌑"
        m=await message.reply_sticker("CAACAgUAAxkBAAEJ90Bm-r1PWvU3dkTvtIEQ_XMebp4uYQACoQgAAqi1gVajGZF7NWM5WR4E") 
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_req_subscribed(client, message):
            try:
                 invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
            except ChatAdminRequired:
                 logger.error("Mᴀᴋᴇ sᴜʀᴇ Bᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ Fᴏʀᴄᴇsᴜʙ ᴄʜᴀɴɴᴇʟ")
                 return
            btn = [[
                InlineKeyboardButton("join update channel", url=invite_link.invite_link)
              ]]
            if message.command[1] != "subscribe":
                try:
                    kk, file_id = message.command[1].split("_", 1)
                    pre = 'checksubp' if kk == 'filep' else 'checksub' 
                    btn.append([InlineKeyboardButton("↻ Tʀʏ Aɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
                except (IndexError, ValueError):
                    btn.append([InlineKeyboardButton("↻ Tʀʏ Aɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
            await client.send_message(
                chat_id=message.from_user.id,
                text="**Yᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ ᴏᴜʀ Bᴀᴄᴋ-ᴜᴘ ᴄʜᴀɴɴᴇʟ ɢɪᴠᴇɴ ʙᴇʟᴏᴡ sᴏ ʏᴏᴜ ᴅᴏɴ'ᴛ ɢᴇᴛ ᴛʜᴇ ᴍᴏᴠɪᴇ ғɪʟᴇ, ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀɴᴅ ᴍᴏᴠɪᴇ ғɪʟᴇ...✅**",
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode=enums.ParseMode.MARKDOWN
                )
            return
        
    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
                    InlineKeyboardButton('☆ Aᴅᴅ Mᴇ Tᴏ Yᴏᴜʀ Gʀᴏᴜᴘ ☆', url=f'http://telegram.me/{temp.U_NAME}?startgroup=true')
                ],[
                    InlineKeyboardButton('Hᴇʟᴘ ⚙️', callback_data='help'),
                    InlineKeyboardButton('Aʙᴏᴜᴛ ✌️', callback_data='about')
                ],[
                    InlineKeyboardButton('Pʀᴇᴍɪᴜᴍ 💳', callback_data="premium_info"),
                    InlineKeyboardButton('Rᴇғᴇʀ ⚜️', callback_data="reffff")
                ],[
                    InlineKeyboardButton('♨️ Gʀᴏᴜᴘ Rᴜʟᴇꜱ ♨️', callback_data="rlu"),
                    InlineKeyboardButton('♻️ Exᴛʀᴀ Fᴇᴀᴛᴜʀᴇꜱ ✅', callback_data='extra')
                ],[
                    InlineKeyboardButton('✇ Jᴏɪɴ Uᴘᴅᴀᴛᴇs Cʜᴀɴɴᴇʟ ✇', callback_data='JoinUᴘᴅᴀᴛᴇs')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "Gᴏᴏᴅ Mᴏʀɴɪɴɢ 🌞" 
        elif curr_time < 17:
            gtxt = "Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ 🌗" 
        elif curr_time < 21:
            gtxt = "Gᴏᴏᴅ Eᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "Gᴏᴏᴅ Nɪɢʜᴛ 🌑"
        m=await message.reply_sticker("CAACAgUAAxkBAAEJ90Bm-r1PWvU3dkTvtIEQ_XMebp4uYQACoQgAAqi1gVajGZF7NWM5WR4E") 
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(message.from_user.mention, gtxt, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
        
    
        
    if message.command[1].startswith("reff_"):
        try:
            user_id = int(message.command[1].split("_")[1])
        except ValueError:
            await message.reply_text("Invalid refer!")
            return
        if user_id == message.from_user.id:
            await message.reply_text("You cannot Refer yourself!")
            return
        if referdb.is_user_in_list(message.from_user.id):
            await message.reply_text("You have been already invited!")
            return
        try:
            uss = await client.get_users(user_id)
        except Exception:
            return 	    
        referdb.add_user(message.from_user.id)
        fromuse = referdb.get_refer_points(user_id) + 10
        if fromuse == 100:
            referdb.add_refer_points(user_id, 0) 
            await message.reply_text(f"You have successfully invited {uss.mention}!")		    
            await message.reply_text(user_id, f"You have been successfully invited by {message.from_user.mention}!") 	
            seconds = 2592000
            if seconds > 0:
                expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}  # Using "id" instead of "user_id"  
                await db.update_user(user_data)  # Use the update_user method to update or insert user data		    
                await client.send_message(
                chat_id=user_id,
                text=f"<b>Hey {uss.mention}\n\nCongratulations you have received 1 month premium subscription for referring 10 users", disable_web_page_preview=True              
                )
            for admin in ADMINS:
                await client.send_message(chat_id=admin, text=f"Successfully completed task by this user:\n\nuser Name: {uss.mention}\n\nuser id: {uss.id}!")	
        else:
            referdb.add_refer_points(user_id, fromuse)
            await message.reply_text(f"You have been successfully invited by {uss.mention}!")
            await client.send_message(user_id, f"You have successfully invited {message.from_user.mention}!")
        return

    if len(message.command) == 2 and message.command[1] in ["premium"]:
        buttons = [[
                    InlineKeyboardButton('📲 Sᴇɴᴅ Pᴀʏᴍᴇɴᴛ Sᴄʀᴇᴇɴꜱʜᴏᴛ', user_id=int(6762558871))
                  ],[
                    InlineKeyboardButton('❌ Cʟᴏꜱᴇ ❌', callback_data='close_data')
                  ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=(SUBSCRIPTION),
            caption=script.PREPLANS_TXT.format(message.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return  
    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("<b>Please wait...</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try: 
                with open(file) as file_data:
                    msgs=json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size=get_size(int(msg.get("size", 0)))
            f_caption=msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🚀 Fᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 🖥️', callback_data=f'stream#{file_id}'),
                            ],
                            [
                                InlineKeyboardButton('📌 Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📌', url=f'https://t.me/CCMTamil') #Don't change anything without contacting me @LazyDeveloperr
                            ]
                        ]
                    )
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton('🚀 Fᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 🖥️', callback_data=f'stream#{file_id}'),
                            ],
                            [
                                InlineKeyboardButton('📌 Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📌', url=f'https://t.me/CCMTamil') #Don't change anything without contacting me @LazyDeveloperr
                            ]
                        ]
                    )
                )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1) 
        await sts.delete()
        return
    
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("<b>Please wait...</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1) 
        return await sts.delete()

    elif data.split("-", 1)[0] == "verify":
        userid = data.split("-", 2)[1]
        token = data.split("-", 3)[2]
        if str(message.from_user.id) != str(userid):
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
        is_valid = await check_token(client, userid, token)
        if is_valid == True:
            await message.reply_text(
                text=f"<b>Hey {message.from_user.mention}, You are successfully verified !\nNow you have unlimited access for all movies till today midnight.</b>",
                protect_content=True
            )
            await verify_user(client, userid, token)
        else:
            return await message.reply_text(
                text="<b>Invalid link or Expired link !</b>",
                protect_content=True
            )
    if data.startswith("sendfiles"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
             gtxt = "Gᴏᴏᴅ Mᴏʀɴɪɴɢ 🌞" 
        elif curr_time < 17:
            gtxt = "Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ 🌗" 
        elif curr_time < 21:
            gtxt = "Gᴏᴏᴅ Eᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "Gᴏᴏᴅ Nɪɢʜᴛ 🌑"
        chat_id = int("-" + file_id.split("-")[1])
        userid = message.from_user.id if message.from_user else None
        g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=allfiles_{file_id}")
        k = await client.send_message(chat_id=message.from_user.id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n‼️ ɢᴇᴛ ᴀʟʟ ꜰɪʟᴇꜱ ɪɴ ᴀ ꜱɪɴɢʟᴇ ʟɪɴᴋ ‼️\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton('📁 Dᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                    ], [
                        InlineKeyboardButton('⚡ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                    ], [
                        InlineKeyboardButton('✨ Bᴜʏ Sᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : Rᴇᴍᴏᴠᴇ Aᴅꜱ ✨', callback_data="seeplans")                        
                    ]
                ]
            )
        )
        await asyncio.sleep(300)
        await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
        
    
    elif data.startswith("short"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "ɢᴏᴏᴅ ᴍᴏʀɴɪɴɢ 👋" 
        elif curr_time < 17:
            gtxt = "ɢᴏᴏᴅ ᴀғᴛᴇʀɴᴏᴏɴ 👋" 
        elif curr_time < 21:
            gtxt = "ɢᴏᴏᴅ ᴇᴠᴇɴɪɴɢ 👋"
        else:
            gtxt = "ɢᴏᴏᴅ ɴɪɢʜᴛ 👋"        
        user_id = message.from_user.id
        chat_id = temp.SHORT.get(user_id)
        files_ = await get_file_details(file_id)
        files = files_[0]
        g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
        k = await client.send_message(chat_id=user_id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n⚠️ ꜰɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n📥 ꜰɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n", reply_markup=InlineKeyboardMarkup(
               [
                    [
                        InlineKeyboardButton('📁 Dᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                    ], [
                        InlineKeyboardButton('⚡ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                    ], [
                        InlineKeyboardButton('✨ Bᴜʏ Sᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : Rᴇᴍᴏᴠᴇ Aᴅꜱ ✨', callback_data="seeplans")                        
                    ]
              ]
        ))
        await asyncio.sleep(600)
        await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
        
    elif data.startswith("all"):
        files = temp.GETALL.get(file_id)
        if not files:
            return await message.reply('<b><i>ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ !</b></i>')
        filesarr = []
        for file in files:
            file_id = file.file_id
            files_ = await get_file_details(file_id)
            files1 = files_[0]
            title = ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1.file_name.split()))
            size=get_size(files1.file_size)
            f_caption=files1.caption
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption=f_caption
            if f_caption is None:
                f_caption = f"{' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files1.file_name.split()))}"
            if not await check_verification(client, message.from_user.id) and VERIFY == True:
                btn = [[
                    InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ ✅", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                ]]
                await message.reply_text(
                    text="<b>ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ !\nᴋɪɴᴅʟʏ ᴠᴇʀɪꜰʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ✅</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                caption=f_caption,
                protect_content=True if pre == 'filep' else False,
                reply_markup=InlineKeyboardMarkup(
            [
             [
              InlineKeyboardButton('🚀 Fᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 🖥️', callback_data=f'stream#{file_id}'),
             ],
             [
              InlineKeyboardButton('📌 Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📌', url=f'https://t.me/CCMTamil') #Don't change anything without contacting me @LazyDeveloperr
             ]
            ]
        )
    )
            filesarr.append(msg)
        k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜᴇꜱᴇ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜᴇꜱᴇ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
        await asyncio.sleep(600)
        for x in filesarr:
            await x.delete()
        await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏꜱ / ꜰɪʟᴇꜱ ᴀʀᴇ ᴅᴇʟᴇᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
        return
        
    elif data.startswith("files"):
        current_time = datetime.now(pytz.timezone(TIMEZONE))
        curr_time = current_time.hour        
        if curr_time < 12:
            gtxt = "Gᴏᴏᴅ Mᴏʀɴɪɴɢ 🌞" 
        elif curr_time < 17:
            gtxt = "Gᴏᴏᴅ Aғᴛᴇʀɴᴏᴏɴ 🌗" 
        elif curr_time < 21:
            gtxt = "Gᴏᴏᴅ Eᴠᴇɴɪɴɢ 🌘"
        else:
            gtxt = "Gᴏᴏᴅ Nɪɢʜᴛ 🌑"        
        user_id = message.from_user.id
        if not await db.has_premium_access(user_id):
            if temp.SHORT.get(user_id)==None:
                return await message.reply_text(text="<b>Please Search Again in Group</b>")
            else:
                chat_id = temp.SHORT.get(user_id)
                settings = await get_settings(chat_id)
                if settings['is_shortlink']:
                    files_ = await get_file_details(file_id)
                    files = files_[0]
                    g = await get_shortlink(chat_id, f"https://telegram.me/{temp.U_NAME}?start=file_{file_id}")
                    k = await client.send_message(chat_id=message.from_user.id,text=f"🫂 ʜᴇʏ {message.from_user.mention}, {gtxt}\n\n✅ ʏᴏᴜʀ ʟɪɴᴋ ɪꜱ ʀᴇᴀᴅʏ, ᴋɪɴᴅʟʏ ᴄʟɪᴄᴋ ᴏɴ ᴅᴏᴡɴʟᴏᴀᴅ ʙᴜᴛᴛᴏɴ.\n\n⚠️ ꜰɪʟᴇ ɴᴀᴍᴇ : <code>{files.file_name}</code> \n\n📥 ꜰɪʟᴇ ꜱɪᴢᴇ : <code>{get_size(files.file_size)}</code>\n\n", reply_markup=InlineKeyboardMarkup(
                        [
                              [
                                    InlineKeyboardButton('📁 Dᴏᴡɴʟᴏᴀᴅ 📁', url=g)
                              ], [
                                    InlineKeyboardButton('⚡ Hᴏᴡ Tᴏ Dᴏᴡɴʟᴏᴀᴅ ⚡', url=await get_tutorial(chat_id))
                              ], [
                                    InlineKeyboardButton('✨ Bᴜʏ Sᴜʙꜱᴄʀɪᴘᴛɪᴏɴ : Rᴇᴍᴏᴠᴇ Aᴅꜱ ✨', callback_data="seeplans")                        
                              ]
                        ]))
                    await asyncio.sleep(600)
                    await k.edit("<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴅᴇʟᴇᴛᴇᴅ !\nᴋɪɴᴅʟʏ ꜱᴇᴀʀᴄʜ ᴀɢᴀɪɴ.</b>")
                    return
    user = message.from_user.id
    files_ = await get_file_details(file_id)           
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            if not await check_verification(client, message.from_user.id) and VERIFY == True:
                btn = [[
                    InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ ✅", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                ]]
                await message.reply_text(
                    text="<b>ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ !\nᴋɪɴᴅʟʏ ᴠᴇʀɪꜰʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ✅</b>",
                    protect_content=True,
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return
            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
                reply_markup=InlineKeyboardMarkup(
            [
             [
              InlineKeyboardButton('🚀 Fᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 🖥️', callback_data=f'stream#{file_id}'),
             ],
             [
              InlineKeyboardButton('📌 Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📌', url=f'https://t.me/CCMTamil') #Don't change anything without contacting me @LazyDeveloperr
             ]
            ]
        )
    )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = '' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), file.file_name.split()))
            size=get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            btn = [[
                InlineKeyboardButton("❗ ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ ❗", callback_data=f'delfile#{file_id}')
            ]]
            k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
            await asyncio.sleep(600)
            await msg.delete()
            await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
            return
        except:
            pass
        return await message.reply('ɴᴏ ꜱᴜᴄʜ ꜰɪʟᴇ ᴇxɪꜱᴛꜱ !')
    files = files_[0]
    title = '' + ' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.split()))
    size=get_size(files.file_size)
    f_caption=files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption=f_caption
    if f_caption is None:
        f_caption = f" {' '.join(filter(lambda x: not x.startswith('[') and not x.startswith('@'), files.file_name.split()))}"
    if not await check_verification(client, message.from_user.id) and VERIFY == True:
        btn = [[
            InlineKeyboardButton("✅ ᴠᴇʀɪꜰʏ ✅", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
        ]]
        await message.reply_text(
            text="<b>ʏᴏᴜ'ʀᴇ ɴᴏᴛ ᴠᴇʀɪꜰɪᴇᴅ !\nᴋɪɴᴅʟʏ ᴠᴇʀɪꜰʏ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ✅</b>",
            protect_content=True,
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    msg = await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
        reply_markup=InlineKeyboardMarkup(
            [
             [
              InlineKeyboardButton('🚀 Fᴀꜱᴛ Dᴏᴡɴʟᴏᴀᴅ / Wᴀᴛᴄʜ Oɴʟɪɴᴇ 🖥️', callback_data=f'stream#{file_id}'),
             ],
             [
              InlineKeyboardButton('📌 Jᴏɪɴ Uᴘᴅᴀᴛᴇꜱ Cʜᴀɴɴᴇʟ 📌', url=f'https://t.me/CCMTamil') #Don't change anything without contacting me @LazyDeveloperr
             ]
            ]
        )
    )
    btn = [[
        InlineKeyboardButton("❗ ɢᴇᴛ ꜰɪʟᴇ ᴀɢᴀɪɴ ❗", callback_data=f'delfile#{file_id}')
    ]]
    k = await client.send_message(chat_id = message.from_user.id, text=f"<b>❗️ <u>ɪᴍᴘᴏʀᴛᴀɴᴛ</u> ❗️</b>\n\n<b>ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴡɪʟʟ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ɪɴ</b> <b><u>10 ᴍɪɴᴜᴛᴇꜱ</u> </b><b>(ᴅᴜᴇ ᴛᴏ ᴄᴏᴘʏʀɪɢʜᴛ ɪꜱꜱᴜᴇꜱ).</b>\n\n<b><i>📌 ᴘʟᴇᴀꜱᴇ ꜰᴏʀᴡᴀʀᴅ ᴛʜɪꜱ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ᴛᴏ ꜱᴏᴍᴇᴡʜᴇʀᴇ ᴇʟꜱᴇ ᴀɴᴅ ꜱᴛᴀʀᴛ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴛʜᴇʀᴇ.</i></b>")
    await asyncio.sleep(600)
    await msg.delete()
    await k.edit_text("<b>ʏᴏᴜʀ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ !!\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ʏᴏᴜʀ ᴅᴇʟᴇᴛᴇᴅ ᴠɪᴅᴇᴏ / ꜰɪʟᴇ 👇</b>",reply_markup=InlineKeyboardMarkup(btn))
    return  

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴛʏᴘᴇ ᴏꜰ ᴄʜᴀɴɴᴇʟꜱ.")

    text = '📑 **ɪɴᴅᴇxᴇᴅ ᴄʜᴀɴɴᴇʟꜱ / ɢʀᴏᴜᴘꜱ ʟɪꜱᴛ :**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**ᴛᴏᴛᴀʟ :** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TELEGRAM BOT.LOG')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("ᴘʀᴏᴄᴇꜱꜱɪɴɢ...⏳", quote=True)
    else:
        await message.reply('ʀᴇᴘʟʏ ᴛᴏ ꜰɪʟᴇ ᴡɪᴛʜ /delete ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ꜰʀᴏᴍ ᴅʙ.', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('ᴛʜɪꜱ ɪꜱ ɴᴏᴛ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ꜰɪʟᴇ ꜰᴏʀᴍᴀᴛ.')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅʙ ✅')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅʙ ✅')
        else:
            # files indexed before https://github.com/EvamariaTG/EvaMaria/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669R39 
            # have original file name.
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('ꜰɪʟᴇ ɪꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ꜰʀᴏᴍ ᴅʙ ✅')
            else:
                await msg.edit('ꜰɪʟᴇ ɪꜱ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅʙ ❌')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'ᴛʜɪꜱ ᴡɪʟʟ ᴅᴇʟᴇᴛᴇ ᴀʟʟ ʏᴏᴜʀ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ !\nᴅᴏ ʏᴏᴜ ꜱᴛɪʟʟ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⚠️ ʏᴇꜱ ⚠️", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❌ ɴᴏ ❌", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('ᴍᴀɪɴᴛᴀɪɴᴇᴅ ʙʏ : ʜᴘ')
    await message.message.edit('ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀʟʟ ɪɴᴅᴇxᴇᴅ ꜰɪʟᴇꜱ ✅')


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ.\nᴜꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ.")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘ !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return
    
    settings = await get_settings(grp_id)

    try:
        if settings['max_btn']:
            settings = await get_settings(grp_id)
    except KeyError:
        await save_group_settings(grp_id, 'max_btn', False)
        settings = await get_settings(grp_id)
    if 'is_shortlink' not in settings.keys():
        await save_group_settings(grp_id, 'is_shortlink', False)
    else:
        pass

    if settings is not None:
        buttons = [        
                [
                InlineKeyboardButton(
                    'ʀᴇꜱᴜʟᴛ ᴘᴀɢᴇ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ʙᴜᴛᴛᴏɴ' if settings["button"] else 'ᴛᴇxᴛ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ꜰɪʟᴇ ꜱᴇɴᴅ ᴍᴏᴅᴇ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'ꜱᴛᴀʀᴛ' if settings["botpm"] else 'ᴀᴜᴛᴏ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ꜰɪʟᴇ ꜱᴇᴄᴜʀᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["file_secure"] else '✘ Oғғ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ɪᴍᴅʙ ᴘᴏꜱᴛᴇʀ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["imdb"] else '✘ Oғғ',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ꜱᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["spell_check"] else '✘ Oғғ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴡᴇʟᴄᴏᴍᴇ ᴍꜱɢ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["welcome"] else '✘ Oғғ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ ᴅᴇʟᴇᴛᴇ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["auto_delete"] else '✘ Oғғ',
                    callback_data=f'setgs#auto_delete#{settings["auto_delete"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴀᴜᴛᴏ ꜰɪʟᴛᴇʀ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["auto_ffilter"] else '✘ Oғғ',
                    callback_data=f'setgs#auto_ffilter#{settings["auto_ffilter"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴍᴀx ʙᴜᴛᴛᴏɴꜱ',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '10' if settings["max_btn"] else f'{MAX_B_TN}',
                    callback_data=f'setgs#max_btn#{settings["max_btn"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ꜱʜᴏʀᴛʟɪɴᴋ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✔ Oɴ' if settings["is_shortlink"] else '✘ Oғғ',
                    callback_data=f'setgs#is_shortlink#{settings["is_shortlink"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton('⇋ ᴄʟᴏꜱᴇ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ⇋', 
                                     callback_data='close_data'
                                     )
            ]
        ]
        

        btn = [[
                InlineKeyboardButton("👤 ᴏᴘᴇɴ ɪɴ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ 👤", callback_data=f"opnsetpm#{grp_id}")
              ],[
                InlineKeyboardButton("👥 ᴏᴘᴇɴ ʜᴇʀᴇ 👥", callback_data=f"opnsetgrp#{grp_id}")
              ]]

        reply_markup = InlineKeyboardMarkup(buttons)
        if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            await message.reply_text(
                text="<b>ᴡʜᴇʀᴇ ᴅᴏ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴏᴘᴇɴ ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ? ⚙️</b>",
                reply_markup=InlineKeyboardMarkup(btn),
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )
        else:
            await message.reply_text(
                text=f"<b>ᴄʜᴀɴɢᴇ ʏᴏᴜʀ ꜱᴇᴛᴛɪɴɢꜱ ꜰᴏʀ {title} ᴀꜱ ʏᴏᴜ ᴡɪꜱʜ ⚙</b>",
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML,
                reply_to_message_id=message.id
            )

# https://t.me/JISSHU_BOTS
# https://t.me/Jisshu_support

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("ᴄʜᴇᴄᴋɪɴɢ ᴛᴇᴍᴘʟᴀᴛᴇ...")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ.\nᴜꜱᴇ /connect {message.chat.id} ɪɴ ᴘᴍ.")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ ꜱᴜʀᴇ ɪ'ᴍ ᴘʀᴇꜱᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘ !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("ɴᴏ ɪɴᴘᴜᴛ !")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʜᴀɴɢᴇᴅ ᴛᴇᴍᴘʟᴀᴛᴇ ꜰᴏʀ <code>{title}</code> ᴛᴏ\n\n{template}")


@Client.on_message((filters.command(["request", "Request"]) | filters.regex("#request") | filters.regex("#Request")) & filters.group)
async def requests(bot, message):
    if REQST_CHANNEL is None or SUPPORT_CHAT_ID is None: return # Must add REQST_CHANNEL and SUPPORT_CHAT_ID to use this feature
    if message.reply_to_message and SUPPORT_CHAT_ID == message.chat.id:
        chat_id = message.chat.id
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        content = message.reply_to_message.text
        try:
            if REQST_CHANNEL is not None:
                btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.reply_to_message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.reply_to_message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>ʏᴏᴜ ᴍᴜꜱᴛ ᴛʏᴘᴇ ᴀʙᴏᴜᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ [ᴍɪɴɪᴍᴜᴍ 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ]. ʀᴇǫᴜᴇꜱᴛꜱ ᴄᴀɴ'ᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
            pass
        
    elif SUPPORT_CHAT_ID == message.chat.id:
        chat_id = message.chat.id
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        content = message.text
        keywords = ["#request", "/request", "#Request", "/Request"]
        for keyword in keywords:
            if keyword in content:
                content = content.replace(keyword, "")
        try:
            if REQST_CHANNEL is not None and len(content) >= 3:
                btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>ʏᴏᴜ ᴍᴜꜱᴛ ᴛʏᴘᴇ ᴀʙᴏᴜᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ [ᴍɪɴɪᴍᴜᴍ 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ]. ʀᴇǫᴜᴇꜱᴛꜱ ᴄᴀɴ'ᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
            pass
     
    elif SUPPORT_CHAT_ID == message.chat.id:
        chat_id = message.chat.id
        reporter = str(message.from_user.id)
        mention = message.from_user.mention
        success = True
        content = message.text
        keywords = ["#request", "/request", "#Request", "/Request"]
        for keyword in keywords:
            if keyword in content:
                content = content.replace(keyword, "")
        try:
            if REQST_CHANNEL is not None and len(content) >= 3:
                btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                reported_post = await bot.send_message(chat_id=REQST_CHANNEL, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                success = True
            elif len(content) >= 3:
                for admin in ADMINS:
                    btn = [[
                        InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{message.link}"),
                        InlineKeyboardButton('ꜱʜᴏᴡ ᴏᴘᴛɪᴏɴꜱ', callback_data=f'show_option#{reporter}')
                      ]]
                    reported_post = await bot.send_message(chat_id=admin, text=f"<b>📝 ʀᴇǫᴜᴇꜱᴛ : <u>{content}</u>\n\n📚 ʀᴇᴘᴏʀᴛᴇᴅ ʙʏ : {mention}\n📖 ʀᴇᴘᴏʀᴛᴇʀ ɪᴅ : {reporter}\n\n©️ ᴛʜᴇ ᴍᴏᴠɪᴇ ᴘʀᴏᴠɪᴅᴇʀ™</b>", reply_markup=InlineKeyboardMarkup(btn))
                    success = True
            else:
                if len(content) < 3:
                    await message.reply_text("<b>ʏᴏᴜ ᴍᴜꜱᴛ ᴛʏᴘᴇ ᴀʙᴏᴜᴛ ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ [ᴍɪɴɪᴍᴜᴍ 3 ᴄʜᴀʀᴀᴄᴛᴇʀꜱ]. ʀᴇǫᴜᴇꜱᴛꜱ ᴄᴀɴ'ᴛ ʙᴇ ᴇᴍᴘᴛʏ.</b>")
            if len(content) < 3:
                success = False
        except Exception as e:
            await message.reply_text(f"Error: {e}")
            pass

    else:
        success = False
    
    if success:
        '''if isinstance(REQST_CHANNEL, (int, str)):
            channels = [REQST_CHANNEL]
        elif isinstance(REQST_CHANNEL, list):
            channels = REQST_CHANNEL
        for channel in channels:
            chat = await bot.get_chat(channel)
        #chat = int(chat)'''
        link = await bot.create_chat_invite_link(int(REQST_CHANNEL))
        btn = [[
                InlineKeyboardButton('ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ', url=link.invite_link),
                InlineKeyboardButton('ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ', url=f"{reported_post.link}")
              ]]
        await message.reply_text("<b>ʏᴏᴜʀ ʀᴇǫᴜᴇꜱᴛ ʜᴀꜱ ʙᴇᴇɴ ᴀᴅᴅᴇᴅ! ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ ꜱᴏᴍᴇ ᴛɪᴍᴇ.\n\nᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ & ᴠɪᴇᴡ ʀᴇǫᴜᴇꜱᴛ.</b>", reply_markup=InlineKeyboardMarkup(btn))
    
@Client.on_message(filters.command("send") & filters.user(ADMINS))
async def send_msg(bot, message):
    if message.reply_to_message:
        target_id = message.text.split(" ", 1)[1]
        out = "Users Saved In DB Are:\n\n"
        success = False
        try:
            user = await bot.get_users(target_id)
            users = await db.get_all_users()
            async for usr in users:
                out += f"{usr['id']}"
                out += '\n'
            if str(user.id) in str(out):
                await message.reply_to_message.copy(int(user.id))
                success = True
            else:
                success = False
            if success:
                await message.reply_text(f"<b>ʏᴏᴜʀ ᴍᴇꜱꜱᴀɢᴇ ʜᴀꜱ ʙᴇᴇɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ꜱᴇɴᴛ ᴛᴏ {user.mention}.</b>")
            else:
                await message.reply_text("<b>ᴛʜɪꜱ ᴜꜱᴇʀ ᴅɪᴅɴ'ᴛ ꜱᴛᴀʀᴛᴇᴅ ᴛʜɪꜱ ʙᴏᴛ ʏᴇᴛ !</b>")
        except Exception as e:
            await message.reply_text(f"<b>Error: {e}</b>")
    else:
        await message.reply_text("<b>ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴀꜱ ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍᴇꜱꜱᴀɢᴇ ᴜꜱɪɴɢ ᴛʜᴇ ᴛᴀʀɢᴇᴛ ᴄʜᴀᴛ ɪᴅ. ꜰᴏʀ ᴇɢ:  /send ᴜꜱᴇʀɪᴅ</b>")

@Client.on_message(filters.command("deletefiles") & filters.user(ADMINS))

async def deletemultiplefiles(bot, message):

    chat_type = message.chat.type

    if chat_type != enums.ChatType.PRIVATE:

        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention},\nᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏɴ'ᴛ ᴡᴏʀᴋ ɪɴ ɢʀᴏᴜᴘꜱ !\nɪᴛ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ᴍʏ ᴘᴍ.</b>")

    else:

        pass

    try:

        keyword = message.text.split(" ", 1)[1]

    except:

        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention},\nɢɪᴠᴇ ᴍᴇ ᴀ ᴋᴇʏᴡᴏʀᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ꜰɪʟᴇꜱ.</b>")

    btn = [[

       InlineKeyboardButton("⚠️ ʏᴇꜱ, ᴄᴏɴᴛɪɴᴜᴇ ⚠️", callback_data=f"killfilesdq#{keyword}")

       ],[

       InlineKeyboardButton("❌ ɴᴏ, ᴀʙᴏʀᴛ ᴏᴘᴇʀᴀᴛɪᴏɴ ❌", callback_data="close_data")

    ]]

    await message.reply_text(

        text="<b>ᴀʀᴇ ʏᴏᴜ ꜱᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ?\nɴᴏᴛᴇ : ᴛʜɪꜱ ᴄᴏᴜʟᴅ ʙᴇ ᴀ ᴅᴇꜱᴛʀᴜᴄᴛɪᴠᴇ ᴅᴇꜱɪᴄɪᴏɴ.</b>",

        reply_markup=InlineKeyboardMarkup(btn),

        parse_mode=enums.ParseMode.HTML

    )

@Client.on_message(filters.command("shortlink"))
async def shortlink(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ, ᴛᴜʀɴ ᴏꜰꜰ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴛʜɪꜱ ᴀɢᴀɪɴ ᴄᴏᴍᴍᴀɴᴅ.")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇꜱꜱ ᴛᴏ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ !\nᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ꜰᴏʀ ɢʀᴏᴜᴘ ᴀᴅᴍɪɴꜱ.</b>")
    else:
        pass
    try:
        command, shortlink_url, api = data.split(" ")
    except:
        return await message.reply_text("<b>ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ !\nɢɪᴠᴇ ᴍᴇ ᴄᴏᴍᴍᴀɴᴅ ᴀʟᴏɴɢ ᴡɪᴛʜ ꜱʜᴏʀᴛɴᴇʀ ᴡᴇʙꜱɪᴛᴇ ᴀɴᴅ ᴀᴘɪ.\n\nꜰᴏʀᴍᴀᴛ : <code>/shortlink krishnalink.com c8dacdff6e91a8e4b4f093fdb4d8ae31bc273c1a</code>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    shortlink_url = re.sub(r"https?://?", "", shortlink_url)
    shortlink_url = re.sub(r"[:/]", "", shortlink_url)
    await save_group_settings(grpid, 'shortlink', shortlink_url)
    await save_group_settings(grpid, 'shortlink_api', api)
    await save_group_settings(grpid, 'is_shortlink', True)
    await reply.edit_text(f"<b>✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ ꜱʜᴏʀᴛʟɪɴᴋ ꜰᴏʀ <code>{title}</code>.\n\nꜱʜᴏʀᴛʟɪɴᴋ ᴡᴇʙꜱɪᴛᴇ : <code>{shortlink_url}</code>\nꜱʜᴏʀᴛʟɪɴᴋ ᴀᴘɪ : <code>{api}</code></b>")

@Client.on_message(filters.command("setshortlinkoff") & filters.user(ADMINS))
async def offshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋꜱ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'is_shortlink', False)
    ENABLE_SHORTLINK = False
    return await message.reply_text("ꜱʜᴏʀᴛʟɪɴᴋ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴅɪꜱᴀʙʟᴇᴅ.")
    
@Client.on_message(filters.command("setshortlinkon") & filters.user(ADMINS))
async def onshortlink(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋꜱ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    await save_group_settings(grpid, 'is_shortlink', True)
    ENABLE_SHORTLINK = True
    return await message.reply_text("ꜱʜᴏʀᴛʟɪɴᴋ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴇɴᴀʙʟᴇᴅ.")


@Client.on_message(filters.command("shortlink_info"))
async def ginfo(bot, message):
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text(f"<b>{message.from_user.mention},\n\nᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ.</b>")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    chat_id=message.chat.id
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
#     if 'shortlink' in settings.keys():
#         su = settings['shortlink']
#         sa = settings['shortlink_api']
#     else:
#         return await message.reply_text("<b>Shortener Url Not Connected\n\nYou can Connect Using /shortlink command</b>")
#     if 'tutorial' in settings.keys():
#         st = settings['tutorial']
#     else:
#         return await message.reply_text("<b>Tutorial Link Not Connected\n\nYou can Connect Using /set_tutorial command</b>")
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ᴏɴʟʏ ɢʀᴏᴜᴘ ᴏᴡɴᴇʀ ᴏʀ ᴀᴅᴍɪɴ ᴄᴀɴ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ !</b>")
    else:
        settings = await get_settings(chat_id) #fetching settings for group
        if 'shortlink' in settings.keys() and 'tutorial' in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            st = settings['tutorial']
            return await message.reply_text(f"<b><u>ᴄᴜʀʀᴇɴᴛ  ꜱᴛᴀᴛᴜꜱ<u> 📊\n\nᴡᴇʙꜱɪᴛᴇ : <code>{su}</code>\n\nᴀᴘɪ : <code>{sa}</code>\n\nᴛᴜᴛᴏʀɪᴀʟ : {st}</b>", disable_web_page_preview=True)
        elif 'shortlink' in settings.keys() and 'tutorial' not in settings.keys():
            su = settings['shortlink']
            sa = settings['shortlink_api']
            return await message.reply_text(f"<b><u>ᴄᴜʀʀᴇɴᴛ  ꜱᴛᴀᴛᴜꜱ<u> 📊\n\nᴡᴇʙꜱɪᴛᴇ : <code>{su}</code>\n\nᴀᴘɪ : <code>{sa}</code>\n\nᴜꜱᴇ /set_tutorial ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ꜱᴇᴛ ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ.")
        elif 'shortlink' not in settings.keys() and 'tutorial' in settings.keys():
            st = settings['tutorial']
            return await message.reply_text(f"<b>ᴛᴜᴛᴏʀɪᴀʟ : <code>{st}</code>\n\nᴜꜱᴇ  /shortlink  ᴄᴏᴍᴍᴀɴᴅ  ᴛᴏ  ᴄᴏɴɴᴇᴄᴛ  ʏᴏᴜʀ  ꜱʜᴏʀᴛɴᴇʀ</b>")
        else:
            return await message.reply_text("ꜱʜᴏʀᴛɴᴇʀ ᴀɴᴅ ᴛᴜᴛᴏʀɪᴀʟ ᴀʀᴇ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ.\n\nᴄʜᴇᴄᴋ /set_tutorial  ᴀɴᴅ  /shortlink  ᴄᴏᴍᴍᴀɴᴅ.")

@Client.on_message(filters.command("set_tutorial"))
async def settutorial(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ, ᴛᴜʀɴ ᴏꜰꜰ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴡᴏʀᴋꜱ ᴏɴʟʏ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return
    else:
        pass
    if len(message.command) == 1:
        return await message.reply("<b>ɢɪᴠᴇ ᴍᴇ ᴀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ᴀʟᴏɴɢ ᴡɪᴛʜ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.\n\nᴜꜱᴀɢᴇ : /set_tutorial <code>https://t.me/HowToOpenHP</code></b>")
    elif len(message.command) == 2:
        reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
        tutorial = message.command[1]
        await save_group_settings(grpid, 'tutorial', tutorial)
        await save_group_settings(grpid, 'is_tutorial', True)
        await reply.edit_text(f"<b>✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴀᴅᴅᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ\n\nʏᴏᴜʀ ɢʀᴏᴜᴘ : {title}\n\nʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ : <code>{tutorial}</code></b>")
    else:
        return await message.reply("<b>ʏᴏᴜ ᴇɴᴛᴇʀᴇᴅ ɪɴᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ !\nᴄᴏʀʀᴇᴄᴛ ꜰᴏʀᴍᴀᴛ : /set_tutorial <code>https://t.me/HowToOpenHP</code></b>")

@Client.on_message(filters.command("remove_tutorial"))
async def removetutorial(bot, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ'ʀᴇ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ, ᴛᴜʀɴ ᴏꜰꜰ ᴀɴᴏɴʏᴍᴏᴜꜱ ᴀᴅᴍɪɴ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.")
    chat_type = message.chat.type
    if chat_type == enums.ChatType.PRIVATE:
        return await message.reply_text("ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴏɴʟʏ ᴡᴏʀᴋꜱ ɪɴ ɢʀᴏᴜᴘꜱ !")
    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grpid = message.chat.id
        title = message.chat.title
    else:
        return
    userid = message.from_user.id
    user = await bot.get_chat_member(grpid, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return
    else:
        pass
    reply = await message.reply_text("<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grpid, 'is_tutorial', False)
    await reply.edit_text(f"<b>ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ✅</b>")

@Client.on_message(filters.command("restart") & filters.user(ADMINS))
async def stop_button(bot, message):
    msg = await bot.send_message(text="<b><i>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛɪɴɢ</i></b>", chat_id=message.chat.id)       
    await asyncio.sleep(3)
    await msg.edit("<b><i><u>ʙᴏᴛ ɪꜱ ʀᴇꜱᴛᴀʀᴛᴇᴅ</u> ✅</i></b>")
    os.execl(sys.executable, sys.executable, *sys.argv)

REREREMGS = [ "🎉", "🔥", "⚡"]
# https://t.me/JISSHU_BOTS
# https://t.me/Jisshu_support
@Client.on_message(filters.command("refer"))
async def refer(bot, message):
    await message.react(emoji=random.choice(REREREMGS), big=True)
    btn = [[
        InlineKeyboardButton('invite link', url=f'https://telegram.me/share/url?url=https://t.me/{bot.me.username}?start=reff_{message.from_user.id}&text=Hello%21%20Experience%20a%20bot%20that%20offers%20a%20vast%20library%20of%20unlimited%20movies%20and%20series.%20%F0%9F%98%83'),
        InlineKeyboardButton(f'⏳ {referdb.get_refer_points(message.from_user.id)}', callback_data='ref_point'),
        InlineKeyboardButton('Close', callback_data='close_data')
    ]]  
    m=await message.reply_sticker("CAACAgQAAxkBAAEkt_Rl_7138tgHJdEsqSNzO5mPWioZDgACGRAAAudLcFGAbsHU3KNJUx4E")      
    await m.delete()
    reply_markup = InlineKeyboardMarkup(btn)
    await message.reply_photo(
            photo=random.choice(REFER_PICS),
            caption=f'👋Hay {message.from_user.mention},\n\nHᴇʀᴇ ɪꜱ ʏᴏᴜʀ ʀᴇғғᴇʀᴀʟ ʟɪɴᴋ:\nhttps://t.me/{bot.me.username}?start=reff_{message.from_user.id}\n\nShare this link with your friends, Each time they join,  you will get 10 refferal points and after 100 points you will get 1 month premium subscription.',
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
    )
@Client.on_message(filters.private & filters.command("pm_search_on"))
async def set_pm_search_on(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return
    
    await db.update_pm_search_status(bot_id, enable=True)
    await message.reply_text("<b><i>✅️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴇɴᴀʙʟᴇᴅ, ꜰʀᴏᴍ ɴᴏᴡ ᴜꜱᴇʀꜱ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</i></b>")

@Client.on_message(filters.private & filters.command("pm_search_off"))
async def set_pm_search_off(client, message):
    user_id = message.from_user.id
    bot_id = client.me.id
    if user_id not in ADMINS:
        await message.delete()
        return
    
    await db.update_pm_search_status(bot_id, enable=False)
    await message.reply_text("<b><i>❌️ ᴘᴍ ꜱᴇᴀʀᴄʜ ᴅɪꜱᴀʙʟᴇᴅ, ꜰʀᴏᴍ ɴᴏᴡ ɴᴏ ᴏɴᴇ ᴄᴀɴ ᴀʙʟᴇ ᴛᴏ ꜱᴇᴀʀᴄʜ ᴍᴏᴠɪᴇ ɪɴ ʙᴏᴛ ᴘᴍ.</i></b>")
    
# https://t.me/JISSHU_BOTS
# https://t.me/Jisshu_support