import os
import requests
import telebot
from telebot import types

# ====== توکن‌ها ======
TELEGRAM_TOKEN = "8799705703:AAG3UUjtHcnTXty-Hn8iXfT8jkhVWa137ck"
AUDD_API_TOKEN = "اینجا_توکن_audd_رو_بذار"
# ===================

bot = telebot.TeleBot(TELEGRAM_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "درود! 🎵\nیک پیام صوتی (Voice) برام بفرست تا آهنگش رو تشخیص بدم.")

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    user_id = message.from_user.id
    msg = bot.reply_to(message, "در حال بررسی پیام صوتی شما... ⏳")
    
    try:
        file_info = bot.get_file(message.voice.file_id)
        file_path = f"voice_{user_id}.ogg"
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(file_path, 'wb') as f:
            f.write(downloaded_file)
        
        # ارسال به AudD
        url = "https://api.audd.io/"
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'api_token': AUDD_API_TOKEN, 'return': 'apple_music,spotify'}
            response = requests.post(url, files=files, data=data)
        os.remove(file_path)
        
        result = response.json()
        if result.get('status') == 'success' and result.get('result'):
            tracks = result['result']
            if not isinstance(tracks, list):
                tracks = [tracks]
            
            if len(tracks) == 1:
                send_track_links(message, tracks[0])
            elif len(tracks) > 1:
                keyboard = types.InlineKeyboardMarkup()
                for i, track in enumerate(tracks[:5]):
                    artist = track.get('artist', 'ناشناس')
                    title = track.get('title', 'بدون نام')
                    btn = types.InlineKeyboardButton(f"{i+1}. {artist} - {title}", callback_data=str(i))
                    keyboard.add(btn)
                user_data[user_id] = tracks
                bot.reply_to(message, "چند نتیجه مشابه پیدا شد. لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=keyboard)
            else:
                bot.reply_to(message, "متأسفم، نتوانستم این آهنگ را تشخیص دهم. 😔")
        else:
            bot.reply_to(message, "خطا در تشخیص آهنگ. لطفاً دوباره امتحان کنید.")
    
    except Exception as e:
        bot.reply_to(message, f"یک خطا رخ داد: {e}")

def send_track_links(message, track):
    artist = track.get('artist', 'ناشناس')
    title = track.get('title', 'بدون نام')
    msg = f"🎵 **{artist} - {title}**\n\n"
    
    apple_music = track.get('apple_music', {})
    spotify = track.get('spotify', {})
    
    if apple_music and apple_music.get('url'):
        msg += f"🍎 [Apple Music]({apple_music['url']})\n"
    if spotify and spotify.get('url'):
        msg += f"🎧 [Spotify]({spotify['url']})\n"
    
    if not apple_music and not spotify and track.get('song_link'):
        msg += f"🔗 [مشاهده در وب]({track['song_link']})"
    
    bot.reply_to(message, msg, parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    tracks = user_data.get(user_id)
    
    if not tracks:
        bot.answer_callback_query(call.id, "نتایج قبلی منقضی شده‌اند.")
        return
    
    try:
        selected_index = int(call.data)
        selected_track = tracks[selected_index]
        send_track_links(call.message, selected_track)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        user_data.pop(user_id, None)
    except (IndexError, ValueError):
        bot.answer_callback_query(call.id, "گزینه نامعتبر.")

if __name__ == '__main__':
    print("ربات در حال اجرا است...")
    bot.infinity_polling()