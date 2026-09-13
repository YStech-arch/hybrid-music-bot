import os
import glob
import subprocess
import uuid
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

YT_DLP = "/home/ec2-user/yt-dlp-env/bin/yt-dlp"
COOKIES = "/home/ec2-user/hybrid-music-bot/telegram_cookies.txt"
DENO = "/home/ec2-user/.deno/bin/deno"


def search_and_download_audio(query, max_duration=600):
    request_dir = os.path.join(
        BASE_DIR,
        "downloads",
        uuid.uuid4().hex
    )
    os.makedirs(request_dir, exist_ok=True)
    local_cookies = os.path.join(request_dir, "cookies.txt")
    shutil.copy2(COOKIES, local_cookies)
    os.chmod(local_cookies, 0o644)

    output_template = os.path.join(
        request_dir,
        "%(title)s.%(ext)s"
    )

    search_target = "ytsearch1:" + str(query)

    cmd = [
        YT_DLP,

        search_target,

        "-f", "bestaudio/best",

        "--cookies", local_cookies,

        "--remote-components",
        "ejs:github",

        "--no-playlist",

        "--max-filesize",
        "25M",

        "--concurrent-fragments",
        "4",

        "-x",
        "--audio-format",
        "m4a",

        "-o",
        output_template,

        "--quiet",
        "--no-warnings"
    ]


    try:
        deno_dir = os.path.join(request_dir, "deno_cache")
        os.makedirs(deno_dir, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if not (k.startswith("NODE_") or k.startswith("PM2_") or k.startswith("pm_") or k in {"vizion", "automation", "autorestart", "autostart", "created_at", "exec_interpreter", "exec_mode", "exit_code", "instance_var", "instances", "kill_retry_time", "km_link", "merge_logs", "name", "namespace", "prev_restart_delay", "restart_time", "status", "treekill", "unique_id", "username", "watch", "windowsHide", "_"})}
        env["DENO_DIR"] = deno_dir

        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=BASE_DIR,
            env=env
        )

        downloaded_files = glob.glob(
            os.path.join(request_dir, "*.m4a")
        )

        if not downloaded_files:
            downloaded_files = glob.glob(
                os.path.join(request_dir, "*.mp4")
            )

        if not downloaded_files:
            error = (
                res.stderr.strip()
                if res.stderr
                else "Lagu tidak ditemukan atau gagal diunduh"
            )

            return {
                "ok": False,
                "error": error,
                "title": "",
                "artist": "",
                "file": "",
                "file_path": ""
            }

        file_path = downloaded_files[0]

        title = os.path.splitext(
            os.path.basename(file_path)
        )[0]

        return {
            "ok": True,
            "title": title,
            "artist": "YouTube",
            "file": os.path.abspath(file_path),
            "file_path": os.path.abspath(file_path),
            "error": ""
        }

    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "error": "yt-dlp timeout setelah 90 detik",
            "title": "",
            "artist": "",
            "file": "",
            "file_path": ""
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "title": "",
            "artist": "",
            "file": "",
            "file_path": ""
        }


def search_and_download_video(query, max_duration=600, quality=720):
    request_dir = os.path.join(
        BASE_DIR,
        "downloads",
        uuid.uuid4().hex
    )
    os.makedirs(request_dir, exist_ok=True)

    local_cookies = os.path.join(request_dir, "cookies.txt")
    shutil.copy2(COOKIES, local_cookies)
    os.chmod(local_cookies, 0o644)

    quality = int(quality)
    if quality not in (480, 720, 1080):
        quality = 720

    search_target = "ytsearch1:" + str(query)

    # + = kualitas tertinggi yang masih memungkinkan dikirim Telegram.
    # Kita batasi ukuran hasil agar tidak terkena HTTP 413.
    if quality == 1080:
        qualities = [1080, 720, 480]
    elif quality == 720:
        qualities = [720, 480]
    else:
        qualities = [480]

    for current_quality in qualities:
        output_template = os.path.join(
            request_dir,
            "%(title)s.%(ext)s"
        )

        format_selector = (
            f"bv*[ext=mp4][vcodec^=avc1][height<={current_quality}]"
            f"+ba[ext=m4a][acodec^=mp4a]"
            f"/b[ext=mp4][vcodec^=avc1][height<={current_quality}]"
            f"/b[ext=mp4]"
        )

        cmd = [
            YT_DLP,
            search_target,
            "-f", format_selector,
            "--merge-output-format", "mp4",
            "--cookies", local_cookies,
            "--remote-components", "ejs:github",
            "--no-playlist",
            "--max-filesize", "48M",
            "-o", output_template,
            "--quiet",
            "--no-warnings"
        ]

        try:
            deno_dir = os.path.join(request_dir, "deno_cache")
            os.makedirs(deno_dir, exist_ok=True)

            env = {
                k: v for k, v in os.environ.items()
                if not (
                    k.startswith("NODE_")
                    or k.startswith("PM2_")
                    or k.startswith("pm_")
                    or k in {
                        "vizion", "automation", "autorestart", "autostart",
                        "created_at", "exec_interpreter", "exec_mode",
                        "exit_code", "instance_var", "instances",
                        "kill_retry_time", "km_link", "merge_logs",
                        "name", "namespace", "prev_restart_delay",
                        "restart_time", "status", "treekill",
                        "unique_id", "username", "watch",
                        "windowsHide", "_"
                    }
                )
            }

            env["DENO_DIR"] = deno_dir

            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=BASE_DIR,
                env=env
            )

            downloaded_files = glob.glob(
                os.path.join(request_dir, "*.mp4")
            )

            if not downloaded_files:
                continue

            video_file = downloaded_files[0]
            file_size = os.path.getsize(video_file)

            # Pastikan hasil akhir benar-benar aman dari batas upload.
            if file_size <= 48 * 1024 * 1024:
                return {
                    "success": True,
                    "file_path": video_file,
                    "quality": current_quality,
                    "size": file_size
                }

            os.remove(video_file)

        except subprocess.TimeoutExpired:
            continue
        except Exception:
            continue

    return {
        "success": False,
        "error": "Tidak ada kualitas video yang cukup kecil untuk dikirim Telegram."
    }
