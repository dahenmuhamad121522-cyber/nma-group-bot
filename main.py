import datetime
import json
import os
import telebot
from telebot import types

TOKEN = "8857631817:AAEHlq30yWOU7bvSj03G1GRm8zdinjqTWuA"
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

ADMIN_CHAT_ID = 6839418105
DATA_FILE = "users_data.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except:
        return {}
  return {}


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# ١. ناردنی نما و پێشوازیکردن بە ناوی بەکارهێنەر
@bot.message_handler(commands=["nma"])
def send_welcome(message):
  user_id = str(message.from_user.id)
  data = load_data()

  if user_id in data and "name" in data[user_id]:
    display_name = data[user_id]["name"]
  else:
    display_name = (
        message.from_user.first_name
        if message.from_user.first_name
        else "بەشداربوو"
    )

  markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
  btn_read = types.KeyboardButton("📚 دانانی ژمارەی خوێندنەوەی لاپەڕەی هەفتە")
  btn_change_name = types.KeyboardButton("✏️ گۆڕینی ناوی بەکارهێنەر")
  markup.add(btn_read, btn_change_name)

  bot.send_message(
      message.chat.id,
      f"بەخێرهاتیت بۆ بۆتی خوێندنەوەی گروپی (نما)، {display_name} ی بەڕێز\n\nتکایە"
      " یەکێک لە دوگمەکانی خوارەوە هەڵبژێرە:",
      reply_markup=markup,
  )


# ٢. گۆڕینی ناوی بەکارهێنەر
@bot.message_handler(
    func=lambda message: message.text == "✏️ گۆڕینی ناوی بەکارهێنەر"
)
def request_new_name(message):
  bot.send_message(
      message.chat.id,
      "تکایە ناوی نوێی خۆت (یاخود ناوی سیانیت) بە نووسین بنووسە:",
  )
  bot.register_next_step_handler(message, save_new_name)


def save_new_name(message):
  user_id = str(message.from_user.id)
  new_name = message.text

  data = load_data()
  if user_id not in data:
    data[user_id] = {"name": new_name, "last_week_submitted": ""}
  else:
    data[user_id]["name"] = new_name

  save_data(data)
  bot.send_message(
      message.chat.id,
      f"دەستخۆش! ناوەکەت بە سەرکەوتوویی گۆڕدرا بۆ: **{new_name}**",
      parse_mode="Markdown",
  )
# ٣. پشکنینی دووشەممە و کات (لە ٩ی بەیانی تا ٧ی ئێوارە)
@bot.message_handler(
    func=lambda message: message.text == "📚 دانانی ژمارەی خوێندنەوەی لاپەڕەی هەفتە"
)
def check_time_and_limit(message):
 now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
  current_day = now.strftime("%A")
  current_hour = now.hour
  current_date_str = now.strftime("%Y-%m-%d")

  # لێرەدا کاتەکە کراوە بۆ ڕۆژی دووشەممە لە کاتژمێر ٦ی بەیانی تا ٤ی عەسر (16:00)
  if current_day != "Monday" or not (6 <= current_hour < 16):
    bot.send_message(
        message.chat.id,
        "❌ ببوورە، تەنها لە ڕۆژانی **دووشەممە** لە کاتژمێر **٦ی بەیانی تا ٤ی"
        " عەسر** دەتوانیت ڕاپۆرتی خوێندنەوە بنێریت.",
        parse_mode="Markdown",
    )
    return

  user_id = str(message.from_user.id)
  data = load_data()

  if (
      user_id in data
      and data[user_id].get("last_week_submitted") == current_date_str
  ):
    bot.send_message(
        message.chat.id,
        "⚠️ تو لەم هەفتەیەدا پێشتر ڕاپۆرتی خوێندنەوەت ناردووە، تەنها هەفتەی"
        " جارێک دەکرێت.",
    )
    return

  bot.send_message(
      message.chat.id,
      "تکایە ژمارەی لاپەڕەی ئەم هەفتەیە بنووسە بە ژمارە (وەک: 100)",
  )
  bot.register_next_step_handler(message, get_pages)# ٤. وەرگرتنی ژمارەی لاپەڕە و پاشان داواکردنی ناوی کتێب
def get_pages(message):
  if not message.text.isdigit():
    bot.send_message(
        message.chat.id,
        "⚠️ تکایە تەنها **ژمارە** بنووسە، دووبارە دوگمەکە دابگرە و هەوڵ بدەرەوە.",
        parse_mode="Markdown",
    )
    return

  user_pages = int(message.text)
  user_id = str(message.from_user.id)
  data = load_data()
  if user_id not in data:
    data[user_id] = {
        "name": message.from_user.first_name,
        "last_week_submitted": "",
    }

  data[user_id]["temp_pages"] = user_pages
  save_data(data)

  bot.send_message(
      message.chat.id,
      "تکایە ناوی کتێب یان بابەتی کتێبەکە بنوسە وەک (ڕۆمان، ئایینی، مێژویی)",
  )
  bot.register_next_step_handler(message, get_book_name_and_finish)


# ٥. وەرگرتنی ناوی کتێب و ناردنی ڕاپۆرت بۆ ئەدمین
def get_book_name_and_finish(message):
  book_info = message.text
  user_id = str(message.from_user.id)
  now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
  current_date_str = now.strftime("%Y-%m-%d")

  data = load_data()
  user_pages = data[user_id].get("temp_pages", 0)

  if "name" in data[user_id]:
    user_name = data[user_id]["name"]
  else:
    user_name = message.from_user.first_name

  data[user_id]["last_week_submitted"] = current_date_str
  save_data(data)

  report_text = (
      f"📊 **ڕاپۆرتی نویی خوێندنەوەی هەفتە**\n👤 ناوی بەکارهێنەر: {user_name}\n🆔"
      f" ئایدی: {user_id}\n📖 ژمارەی لاپەڕەکان: {user_pages}\n📚 ناوی کتێب /"
      f" بابەت: {book_info}"
  )

  bot.send_message(ADMIN_CHAT_ID, report_text, parse_mode="Markdown")

  bot.send_message(
      message.chat.id,
      "سوپاس! ڕاپۆرتی خوێندنەوەی ئەم هەفتەت بە سەرکەوتوویی تۆمار کراو بۆ"
      " بەڕێوەبەر نێردرا.",
  )


print("Bot is running...")
bot.infinity_polling()
