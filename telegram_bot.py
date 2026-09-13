from dotenv import load_dotenv
load_dotenv()

import os
import telebot

from core.music import search_and_download_audio, search_and_download_video

TOKEN = os.getenv("YUKI_BOT")

if not TOKEN:
    raise RuntimeError("YUKI_BOT belum diset di environment variable.")

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(func=lambda message: message.text and message.text.split()[0].split('@')[0].lower() in ['/start', '/help'])
def handle_help(message):
    teks = (
        "📌 *Menu Bantuan Bot Yuki*\n\n"
        "• `/play [judul]` : Cari & kirim musik dari YouTube\n"
        "• `/vplay [judul]` : Cari & kirim video dari YouTube\n"

        "• `/lyric [judul]` : Cari lirik lagu\n"
        "• `/stop` : Status & reset bot\n\n"
        "🎵 Sumber musik: YouTube (yt-dlp)"
    )

    bot.reply_to(
        message,
        teks,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: message.text and message.text.split()[0].split('@')[0].lower() == '/play')
def handle_play_cmd(message):
    query = message.text.replace('/play', '', 1).strip()

    if not query:
        bot.reply_to(
            message,
            "Ketik judul lagunya!\n\n"
            "Contoh:\n"
            "`/play lullaby`",
            parse_mode='Markdown'
        )
        return

    msg = bot.reply_to(
        message,
        f"🔍 Mencari di YouTube: *{query}*...",
        parse_mode='Markdown'
    )

    result = None

    try:
        result = search_and_download_audio(query)

        if not result or not result.get("ok") or not result.get("file"):
            error = result.get("error", "Tidak ada detail error") if result else "Result kosong"
            print(f"❌ yt-dlp ERROR: {error}", flush=True)

            bot.edit_message_text(
                f"❌ Gagal mengambil audio.\\n\\n`{error[:800]}`",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="Markdown"
            )
            return

        file_path = result["file"]
        title = result["title"]
        artist = result["artist"]

        bot.edit_message_text(
            f"📤 Mengirim:\n🎵 *{title}*\n👤 {artist}",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='Markdown'
        )

        with open(file_path, 'rb') as audio:
            bot.send_audio(
                message.chat.id,
                audio,
                caption=f"🎵 {title}\n👤 {artist}\n\n🤖 Yuki Bot",
                performer=artist,
                title=title
            )

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:
        print(f"❌ Play Error: {e}")

        try:
            bot.edit_message_text(
                f"❌ Terjadi error:\n`{str(e)[:500]}`",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode='Markdown'
            )
        except Exception:
            pass

    finally:
        # Hapus file temporary setelah dikirim
        if result:
            file_path = result.get("file")

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)

                    # Hapus folder temporary jika kosong
                    temp_dir = os.path.dirname(file_path)

                    if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)

                except Exception as e:
                    print(f"⚠️ Gagal membersihkan file: {e}")



@bot.message_handler(func=lambda message: message.text and message.text.split()[0].split('@')[0].lower() == '/vplay')
def handle_vplay_cmd(message):
    parts = message.text.split(maxsplit=1)
    raw_query = parts[1].strip() if len(parts) > 1 else ""

    quality = 720

    if raw_query.endswith("+"):
        quality = 1080
        query = raw_query[:-1].rstrip()
    elif raw_query.endswith("-"):
        quality = 480
        query = raw_query[:-1].rstrip()
    else:
        query = raw_query

    if not query:
        bot.reply_to(
            message,
            "Ketik judul videonya!\n\n"
            "Contoh:\n"
            "`/vplay Alan Walker Faded`",
            parse_mode='Markdown'
        )
        return

    msg = bot.reply_to(
        message,
        f"🔍 Mencari video di YouTube: *{query}*...",
        parse_mode='Markdown'
    )

    result = None

    try:
        result = search_and_download_video(query, quality=quality)

        if not result or not result.get("success") or not result.get("file_path"):
            error = result.get("error", "Video tidak ditemukan atau gagal diunduh") if result else "Result kosong"
            print(f"❌ Video ERROR: {error}", flush=True)

            bot.edit_message_text(
                f"❌ Gagal mengambil video.\n\n`{str(error)[:800]}`",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode="Markdown"
            )
            return

        file_path = result["file_path"]
        title = os.path.basename(file_path).rsplit(".", 1)[0]

        bot.edit_message_text(
            f"📤 Mengirim video:\n🎬 *{title}*",
            chat_id=message.chat.id,
            message_id=msg.message_id,
            parse_mode='Markdown'
        )

        with open(file_path, 'rb') as video:
            bot.send_video(
                message.chat.id,
                video,
                caption=f"🎬 {title}\n\n🤖 Yuki Bot"
            )

        bot.delete_message(
            message.chat.id,
            msg.message_id
        )

    except Exception as e:
        print(f"❌ VPlay Error: {e}", flush=True)

        try:
            bot.edit_message_text(
                f"❌ Terjadi error:\n`{str(e)[:500]}`",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode='Markdown'
            )
        except Exception:
            pass

    finally:
        if result:
            file_path = result.get("file_path")

            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)

                    temp_dir = os.path.dirname(file_path)

                    if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)

                except Exception as e:
                    print(f"⚠️ Gagal membersihkan video: {e}", flush=True)


@bot.message_handler(func=lambda message: message.text and message.text.split()[0].split('@')[0].lower() == '/stop')
def handle_stop(message):
    bot.reply_to(
        message,
        "⏹️ Proses sebelumnya dibatalkan. "
        "Yuki kembali siaga!",
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: True)
def handle_text(message):
    teks = message.text.lower().strip()

    if teks.startswith('putar '):
        query = message.text[6:].strip()

        message.text = f"/play {query}"

        handle_play_cmd(message)

    else:
        bot.reply_to(
            message,
            "Yuki di sini! Ketik `/help` untuk daftar perintah "
            "atau ketik `/play [judul]`.",
            parse_mode='Markdown'
        )


if __name__ == '__main__':
    print("✅ Bot Yuki Siap!")
    print("🎵 Music source: YouTube (yt-dlp)")
    bot.infinity_polling()
