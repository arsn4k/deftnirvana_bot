import os
import json
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes


TOKEN = "8749307543:AAGQoh4KO3gluso9Dm8pX_EkOK_f6y2ePNM"

STATE_FILE = "state.json"
PHOTOS_DIR = "photos"

BANDS = {
    "deftones": {"emoji": "🎸", "name": "Deftones"},
    "nirvana":  {"emoji": "💀", "name": "Nirvana"},
}

#Стан

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {band: {"used": [], "last_reset": ""} for band in BANDS}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

#Фото

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

    used = state[band]["used"]
    available = [p for p in all_photos if p not in used]

    # Всі показані — скидаємо цикл
    if not available:
        state[band]["used"] = []
        state[band]["last_reset"] = datetime.now().isoformat()
        available = all_photos

    chosen = random.choice(available)
    state[band]["used"].append(chosen)
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
        "Фотографії не повторюються, поки всі не будуть показані.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_stats(update.message.reply_text)

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
        state_fresh = load_state()
        lines = ["📊 *Статистика фото:*\n"]
        for band, info in BANDS.items():
            used  = len(state_fresh[band]["used"])
            total = len(get_all_photos(band))
            remaining = total - used
            lines.append(f"{info['emoji']} *{info['name']}*: показано {used}/{total} — залишилось {remaining}")
        await query.message.reply_text("\n".join(lines), parse_mode="Markdown")
        return

    save_state(state)

    # Кнопки після фото
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

    photo_path = os.path.join(PHOTOS_DIR, band, photo_name)
    used_count  = len(state[band]["used"])
    total_count = len(get_all_photos(band))

    caption = (
        f"{info['emoji']} *{info['name']}*\n"
        f"📸 Показано: {used_count}/{total_count}"
    )

    with open(photo_path, "rb") as f:
        await message.reply_photo(photo=f, caption=caption, parse_mode="Markdown")

async def send_stats(reply_fn):
    state = load_state()
    lines = ["📊 *Статистика фото:*\n"]
    for band, info in BANDS.items():
        used  = len(state[band]["used"])
        total = len(get_all_photos(band))
        lines.append(f"{info['emoji']} *{info['name']}*: {used}/{total} показано")
    await reply_fn("\n".join(lines), parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  start))
    app.add_handler(CommandHandler("stats",  cmd_stats))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("✅ Бот запущено! Натисни Ctrl+C щоб зупинити.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()