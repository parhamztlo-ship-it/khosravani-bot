import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ====== توکن‌ها رو اینجا وارد کن ======
TELEGRAM_TOKEN = "8799705703:AAG3UUjtHcnTXty-Hn8iXfT8jkhvWa137ck"
AUDD_API_TOKEN = "اینجا_توکن_audd_رو_بذار"
# ===================================

user_search_results = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! 🎵\nیک پیام صوتی (Voice) برام بفرست تا آهنگش رو تشخیص بدم.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("در حال بررسی پیام صوتی شما... ⏳")

    try:
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_path = f"voice_{user_id}.ogg"
        await file.download_to_drive(file_path)

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
                await send_track_links(update, tracks[0])
            elif len(tracks) > 1:
                keyboard = []
                for i, track in enumerate(tracks[:5]):
                    artist = track.get('artist', 'ناشناس')
                    title = track.get('title', 'بدون نام')
                    button_text = f"{i+1}. {artist} - {title}"
                    keyboard.append([InlineKeyboardButton(button_text, callback_data=str(i))])
                reply_markup = InlineKeyboardMarkup(keyboard)
                user_search_results[user_id] = tracks
                await update.message.reply_text("چند نتیجه مشابه پیدا شد. لطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=reply_markup)
            else:
                await update.message.reply_text("متأسفم، نتوانستم این آهنگ را تشخیص دهم. 😔")
        else:
            await update.message.reply_text("خطا در تشخیص آهنگ. لطفاً دوباره امتحان کنید.")

    except Exception as e:
        await update.message.reply_text(f"یک خطا رخ داد: {e}")

async def send_track_links(update, track):
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

    await update.message.reply_text(msg, parse_mode='Markdown')

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    tracks = user_search_results.get(user_id)

    if not tracks:
        await query.edit_message_text("نتایج قبلی منقضی شده‌اند. لطفاً دوباره پیام صوتی بفرستید.")
        return

    try:
        selected_index = int(query.data)
        selected_track = tracks[selected_index]
        await send_track_links(update, selected_track)
        await query.edit_message_reply_markup(reply_markup=None)
        user_search_results.pop(user_id, None)
    except (IndexError, ValueError):
        await query.edit_message_text("گزینه نامعتبر. لطفاً دوباره امتحان کنید.")

if __name__ == '__main__':
    print("ربات در حال اجرا است...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # استفاده از webhook به جای polling برای Render
    port = int(os.environ.get('PORT', 10000))
    app.run_webhook(listen="0.0.0.0", port=port, 
                    webhook_url="https://khosravani-music-bot.onrender.com/")