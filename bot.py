import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import logging
from telegram.error import NetworkError, TimedOut

TOKEN = os.environ.get("BOT_TOKEN", "")

STATE_FILE = "state.json"
PHOTOS_DIR = "photos"

#text samples for each band, you can add more variations if you want
BANDS = {
    "deftones": {
        "emoji": "🎸",
        "name": "Deftones",
        "texts": [
            "wish I knew deftones before they were popular",
            "wish I found deftones before everyone else did",
            "wish I discovered deftones before they blew up",
            "wish I got into deftones before they went mainstream",
            "wish I heard deftones before they went viral",
            "wish I knew deftones when they were still underground",
            "wish I liked deftones before it was cool",
            "wish I knew deftones back when no one talked about them",
            "wish I discovered deftones before they were everywhere",
            "wish I found deftones when they still felt like a secret",
            "wish I experienced deftones before the hype",
            "wish I knew deftones before they had millions of listeners",
            "wish I knew deftones before they got popular",
            "wish I knew deftones before they were famous",
        ],
    },
    "nirvana": {
        "emoji": "💀",
        "name": "Nirvana",
        "texts": [
            "wish I knew nirvana before they were popular",
            "wish I found nirvana before everyone else did",
            "wish I discovered nirvana before they blew up",
            "wish I got into nirvana before they went mainstream",
            "wish I heard nirvana before they went viral",
            "wish I knew nirvana when they were still underground",
            "wish I liked nirvana before it was cool",
            "wish I knew nirvana back when no one talked about them",
            "wish I discovered nirvana before they were everywhere",
            "wish I found nirvana when they still felt like a secret",
            "wish I experienced nirvana before the hype",
            "wish I knew nirvana before they had millions of listeners",
            "wish I knew nirvana before they got popular",
            "wish I knew nirvana before they were famous",
        ],
    },
}

# Стан

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        band: {"used_photos": [], "used_texts": [], "last_reset": ""}
        for band in BANDS
    }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# Фото

def get_all_photos(band: str) -> list:
    folder = os.path.join(PHOTOS_DIR, band)
    if not os.path.exists(folder):
        return []
    return [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
    ]

def get_next_photo(band: str, state: dict) -> str | None:
    all_photos = get_all_photos(band)
    if not all_photos:
        return None

    used = state[band]["used_photos"]
    available = [p for p in all_photos if p not in used]

    if not available:
        state[band]["used_photos"] = []
        state[band]["last_reset"] = datetime.now().isoformat()
        available = all_photos

    chosen = random.choice(available)
    state[band]["used_photos"].append(chosen)
    return chosen

def get_next_text(band: str, state: dict) -> str:
    all_texts = BANDS[band]["texts"]

    used = state[band]["used_texts"]
    available = [t for t in all_texts if t not in used]

    if not available:
        state[band]["used_texts"] = []
        available = all_texts

    chosen = random.choice(available)
    state[band]["used_texts"].append(chosen)
    return chosen

# Хендлери

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🎸 Deftones", callback_data="photo_deftones"),
            InlineKeyboardButton("💀 Nirvana",  callback_data="photo_nirvana"),
        ],
        [InlineKeyboardButton("🎵 Обидва гурти", callback_data="photo_both")],
        [InlineKeyboardButton("📊 Статистика",   callback_data="stats")],
    ]
    await update.message.reply_text(
        "🎶 *Deftones & Nirvana Photo Bot*\n\n"
        "Обери гурт — отримаєш нове фото.\n"
        "Фотографії та тексти не повторюються, поки всі не будуть показані.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = load_state()
    lines = ["📊 *Статистика:*\n"]
    for band, info in BANDS.items():
        used_p = len(state[band]["used_photos"])
        total_p = len(get_all_photos(band))
        used_t = len(state[band]["used_texts"])
        total_t = len(info["texts"])
        lines.append(
            f"{info['emoji']} *{info['name']}*\n"
            f"  📸 Фото: {used_p}/{total_p}\n"
            f"  💬 Тексти: {used_t}/{total_t}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    state = load_state()
    data  = query.data

    if data == "photo_both":
        for band in BANDS:
            await send_band_photo(query.message, band, state)
    elif data.startswith("photo_"):
        band = data.replace("photo_", "")
        await send_band_photo(query.message, band, state)
    elif data == "stats":
        lines = ["📊 *Статистика:*\n"]
        for band, info in BANDS.items():
            used_p = len(state[band]["used_photos"])
            total_p = len(get_all_photos(band))
            used_t = len(state[band]["used_texts"])
            total_t = len(info["texts"])
            lines.append(
                f"{info['emoji']} *{info['name']}*\n"
                f"  📸 Фото: {used_p}/{total_p}\n"
                f"  💬 Тексти: {used_t}/{total_t}"
            )
        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    save_state(state)

    keyboard = [
        [
            InlineKeyboardButton("🎸 Ще Deftones", callback_data="photo_deftones"),
            InlineKeyboardButton("💀 Ще Nirvana",  callback_data="photo_nirvana"),
        ],
        [InlineKeyboardButton("🎵 Обидва", callback_data="photo_both")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
    ]
    await query.message.reply_text(
        "Натисни кнопку для наступного фото:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

async def send_band_photo(message, band: str, state: dict):
    info = BANDS[band]
    photo_name = get_next_photo(band, state)

    if not photo_name:
        await message.reply_text(
            f"❌ Фото для {info['name']} не знайдено.\n"
            f"Додай зображення у папку `photos/{band}/`",
            parse_mode="Markdown",
        )
        return

    text = get_next_text(band, state)
    photo_path = os.path.join(PHOTOS_DIR, band, photo_name)
    used_count  = len(state[band]["used_photos"])
    total_count = len(get_all_photos(band))

    caption = (
        f"{info['emoji']} *{info['name']}*\n"
        f"📸 {used_count}/{total_count}\n\n"
        f"_{text}_"
    )

    with open(photo_path, "rb") as f:
        await message.reply_photo(photo=f, caption=caption, parse_mode="Markdown")

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(context.error, (NetworkError, TimedOut)):
        # Мережеві помилки — ігноруємо, бот сам відновиться
        return
    # Інші помилки — логуємо
    logging.error("Помилка:", exc_info=context.error)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_error_handler(error_handler)  # ← додай це
    print("✅ Бот запущено! Натисни Ctrl+C щоб зупинити.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()