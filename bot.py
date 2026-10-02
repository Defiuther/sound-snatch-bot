import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import yt_dlp

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "8695098861:AAG5Qu-sP_zx959VUhXxQjHcdRZMC6GUAB8"
DOWNLOAD_DIR = "downloads"

# ============ ИНИЦИАЛИЗАЦИЯ ============
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ============ ХЕЛПЕРЫ ============
def download_audio(url: str) -> str:
    """Скачивает аудио с YouTube/TikTok/etc и конвертирует в MP3"""
    output_template = os.path.join(DOWNLOAD_DIR, "%(title)s.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_template,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # Меняем расширение на .mp3
        mp3_file = os.path.splitext(filename)[0] + '.mp3'
        return mp3_file

# ============ ХЕНДЛЕРЫ ============
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎵 **SoundSnatch Bot**\n\n"
        "Пришли мне ссылку на видео (YouTube, TikTok, Instagram, SoundCloud) "
        "— я скачаю и отправлю тебе **MP3**!\n\n"
        "Просто вставь ссылку в чат 👇",
        parse_mode="Markdown"
    )

@dp.message(F.text.startswith("http"))
async def handle_url(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("⏳ Скачиваю и конвертирую...")

    try:
        # Скачиваем в отдельном потоке, чтобы не блокировать бота
        loop = asyncio.get_event_loop()
        mp3_path = await loop.run_in_executor(None, download_audio, url)

        if not os.path.exists(mp3_path):
            await status_msg.edit_text("❌ Не удалось найти MP3-файл")
            return

        # Отправляем файл
        audio_file = FSInputFile(mp3_path)
        await message.answer_audio(audio_file, title=os.path.basename(mp3_path))
        await status_msg.delete()

        # Удаляем файл после отправки
        os.remove(mp3_path)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await status_msg.edit_text(f"❌ Ошибка: {str(e)[:200]}")

@dp.message()
async def handle_other(message: Message):
    await message.answer("🤔 Пришли мне ссылку (начинается с http), и я скачаю MP3!")

# ============ ЗАПУСК ============
async def main():
    print("🎵 SoundSnatch Bot запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())