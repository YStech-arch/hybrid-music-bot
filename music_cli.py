import sys
import json
import os
import shutil

from core.music import search_and_download_audio


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "ok": False,
            "error": "Query lagu kosong"
        }))
        return

    query = " ".join(sys.argv[1:]).strip()

    if not query:
        print(json.dumps({
            "ok": False,
            "error": "Query lagu kosong"
        }))
        return

    try:
        result = search_and_download_audio(query)

        if not result:
            print(json.dumps({
                "ok": False,
                "error": "Lagu tidak ditemukan atau terlalu besar"
            }))
            return

        if not result.get("ok") or not result.get("file"):
            print(json.dumps({
                "ok": False,
                "file": "",
                "title": "",
                "artist": "",
                "error": result.get("error", "Download gagal")
            }))
            return

        print(json.dumps({
            "ok": True,
            "file": result["file"],
            "title": result["title"],
            "artist": result["artist"]
        }))

    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": str(e)
        }))


if __name__ == "__main__":
    main()
