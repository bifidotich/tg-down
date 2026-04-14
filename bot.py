import os
import re
import asyncio
import logging
import time
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!.")

DOWNLOAD_DIR = "/app/downloads"
COOKIES_FILE = "/app/cookies.txt"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Регулярные выражения
YT_PATTERN = r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$'
TT_PATTERN = r'^(https?\:\/\/)?(www\.)?((vt|vm)\.)?tiktok\.com\/.+$'
IG_PATTERN = r'^(https?\:\/\/)?(www\.)?(instagram\.com)\/.+$'


def is_valid_url(url: str) -> bool:
    return bool(re.match(YT_PATTERN, url) or re.match(TT_PATTERN, url) or re.match(IG_PATTERN, url))


def download_media_sync(url: str) -> str:
    ydl_opts = {
        'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
        'format': 'best[filesize<50M]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True
    }

    # Если файл с куки существует
    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


async def auto_clear_cache():
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(DOWNLOAD_DIR):
                file_path = os.path.join(DOWNLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    if current_time - os.path.getctime(file_path) > 3600:
                        os.remove(file_path)
                        logger.info(f"Кэш очищен: удален {file_path}")
        except Exception as e:
            logger.error(f"Ошибка при очистке кэша: {e}")
        await asyncio.sleep(1800)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Отправь ссылку на видео YouTube, TikTok или Instagram, и я скачаю его.")


@dp.message(F.text)
async def handle_message(message: Message):
    url = message.text.strip()

    if not is_valid_url(url):
        await message.answer("Пожалуйста, отправьте корректную ссылку на YouTube, TikTok или Instagram.")
        return

    wait_msg = await message.answer("⏳ Загружаю видео...")
    file_path = None

    try:
        file_path = await asyncio.to_thread(download_media_sync, url)
        video = FSInputFile(file_path)
        await bot.send_video(chat_id=message.chat.id, video=video)
        await wait_msg.delete()

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if "login" in error_msg or "cookie" in error_msg:
            await wait_msg.edit_text("❌ Ошибка: Для загрузки этого видео из Instagram требуется авторизация.")
        else:
            await wait_msg.edit_text("❌ Ошибка загрузки. Возможно, видео недоступно, приватно или слишком большое.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await wait_msg.edit_text("❌ Произошла непредвиденная ошибка.")

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Не удалось удалить файл {file_path}: {e}")


async def main():
    asyncio.create_task(auto_clear_cache())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())