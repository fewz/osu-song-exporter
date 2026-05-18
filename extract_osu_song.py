# main.py

import shutil
import re
import json
import importlib.util
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# =========================================================
# LOAD CONFIG
# =========================================================

CONFIG_FILE = "config.py"

spec = importlib.util.spec_from_file_location(
    "config",
    CONFIG_FILE
)

config = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config)

# =========================================================

db_lock = Lock()

# JSON database di folder script python saat ini
SCRIPT_DIR = Path(__file__).parent
DATABASE_PATH = SCRIPT_DIR / "exported_songs.json"


def sanitize_filename(name):

    if not name:
        return "Unknown"

    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()

    return name if name else "Unknown"


def parse_osu_file(osu_file):

    encodings = ["utf-8", "utf-8-sig"]

    for enc in encodings:

        try:

            title = None
            artist = None
            audio = None
            background = None

            in_events = False

            with open(osu_file, "r", encoding=enc) as f:

                for line in f:

                    line = line.strip()

                    # ======================================
                    # TITLE
                    # ======================================

                    if line.startswith("TitleUnicode:"):

                        value = line.replace(
                            "TitleUnicode:",
                            ""
                        ).strip()

                        if value:
                            title = value

                    elif line.startswith("Title:") and not title:

                        title = line.replace(
                            "Title:",
                            ""
                        ).strip()

                    # ======================================
                    # ARTIST
                    # ======================================

                    if line.startswith("ArtistUnicode:"):

                        value = line.replace(
                            "ArtistUnicode:",
                            ""
                        ).strip()

                        if value:
                            artist = value

                    elif line.startswith("Artist:") and not artist:

                        artist = line.replace(
                            "Artist:",
                            ""
                        ).strip()

                    # ======================================
                    # AUDIO
                    # ======================================

                    elif line.startswith("AudioFilename:"):

                        audio = line.replace(
                            "AudioFilename:",
                            ""
                        ).strip()

                    # ======================================
                    # EVENTS
                    # ======================================

                    elif line.startswith("[Events]"):

                        in_events = True

                    elif line.startswith("[") and line != "[Events]":

                        in_events = False

                    # ======================================
                    # BACKGROUND
                    # ======================================

                    elif in_events and not background:

                        if line.startswith("0,0,"):

                            match = re.search(
                                r'"(.+?)"',
                                line
                            )

                            if match:
                                background = match.group(1)

            if title and artist and audio:

                return {
                    "title": title,
                    "artist": artist,
                    "audio": audio,
                    "background": background
                }

        except:
            pass

    return None


def generate_song_key(artist, title):

    return f"{artist.lower()}::{title.lower()}"


def load_database():

    if config.REFRESH_DATABASE:
        return {}

    if not DATABASE_PATH.exists():
        return {}

    try:

        with open(
            DATABASE_PATH,
            "r",
            encoding="utf-8"
        ) as f:

            return json.load(f)

    except:
        return {}


def save_database(database):

    with open(
        DATABASE_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            database,
            f,
            ensure_ascii=False,
            indent=4
        )


def process_folder(folder, database, export_root):

    try:

        osu_files = list(folder.glob("*.osu"))

        if not osu_files:
            return None

        metadata = None

        for osu_file in osu_files:

            metadata = parse_osu_file(osu_file)

            if metadata:
                break

        if not metadata:
            return None

        title = metadata["title"]
        artist = metadata["artist"]

        song_key = generate_song_key(artist, title)

        # ==========================================
        # CHECK DATABASE
        # ==========================================

        with db_lock:

            if song_key in database:

                return {
                    "status": "skip",
                    "artist": artist,
                    "title": title
                }

        audio_file = folder / metadata["audio"]

        if not audio_file.exists():
            return None

        # ==========================================
        # OUTPUT
        # ==========================================

        safe_artist = sanitize_filename(artist)
        safe_title = sanitize_filename(title)

        artist_folder = export_root / safe_artist
        artist_folder.mkdir(parents=True, exist_ok=True)

        ext = audio_file.suffix

        output_audio = artist_folder / f"{safe_title}{ext}"

        counter = 1

        while output_audio.exists():

            output_audio = (
                artist_folder /
                f"{safe_title} ({counter}){ext}"
            )

            counter += 1

        # ==========================================
        # COPY / MOVE
        # ==========================================

        if config.COPY_MODE:
            shutil.copy2(audio_file, output_audio)
        else:
            shutil.move(audio_file, output_audio)

        # ==========================================
        # BACKGROUND
        # ==========================================

        if (
            config.EXPORT_BACKGROUND and
            metadata["background"]
        ):

            bg_file = folder / metadata["background"]

            if bg_file.exists():

                bg_ext = bg_file.suffix

                output_bg = (
                    artist_folder /
                    f"{safe_title}_cover{bg_ext}"
                )

                try:
                    shutil.copy2(bg_file, output_bg)
                except:
                    pass

        # ==========================================
        # SAVE DATABASE
        # ==========================================

        with db_lock:

            database[song_key] = {
                "artist": artist,
                "title": title,
                "audio": str(output_audio)
            }

        return {
            "status": "export",
            "artist": artist,
            "title": title
        }

    except Exception as e:

        print(f"[ERROR] {folder.name}")
        print(e)

        return None


def generate_playlist(database, export_root):

    # ==========================================
    # GLOBAL PLAYLIST
    # ==========================================

    global_playlist = export_root / "playlist.m3u"

    with open(global_playlist, "w", encoding="utf-8") as f:

        f.write("#EXTM3U\n")

        for item in database.values():

            audio_path = Path(item["audio"])

            if audio_path.exists():

                rel = audio_path.relative_to(export_root)

                f.write(str(rel) + "\n")

    # ==========================================
    # ARTIST PLAYLIST
    # ==========================================

    artist_map = {}

    for item in database.values():

        artist_map.setdefault(
            item["artist"],
            []
        ).append(item)

    for artist, songs in artist_map.items():

        safe_artist = sanitize_filename(artist)

        artist_folder = export_root / safe_artist

        playlist = artist_folder / "playlist.m3u"

        with open(playlist, "w", encoding="utf-8") as f:

            f.write("#EXTM3U\n")

            for song in songs:

                audio_path = Path(song["audio"])

                if audio_path.exists():

                    f.write(audio_path.name + "\n")


def main():

    export_root = Path(config.EXPORT_FOLDER)
    export_root.mkdir(parents=True, exist_ok=True)

    database = load_database()

    songs_path = Path(config.OSU_SONGS_FOLDER)

    folders = [
        f for f in songs_path.iterdir()
        if f.is_dir()
    ]

    if config.LIMIT is not None:
        folders = folders[:config.LIMIT]

    print(f"Folder scan : {len(folders)}")
    print(f"Database    : {len(database)}")
    print(f"Workers     : {config.MAX_WORKERS}")
    print()

    exported = 0
    skipped = 0

    with ThreadPoolExecutor(
        max_workers=config.MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                process_folder,
                folder,
                database,
                export_root
            )
            for folder in folders
        ]

        for future in as_completed(futures):

            result = future.result()

            if not result:
                continue

            if result["status"] == "skip":

                skipped += 1

                print(
                    f"[SKIP] "
                    f"{result['artist']} - {result['title']}"
                )

            elif result["status"] == "export":

                exported += 1

                print(
                    f"[EXPORT] "
                    f"{result['artist']} - {result['title']}"
                )

    # ==========================================
    # SAVE DATABASE
    # ==========================================

    save_database(database)

    # ==========================================
    # PLAYLIST
    # ==========================================

    if config.GENERATE_PLAYLIST:
        generate_playlist(database, export_root)

    print("\n====================================")
    print(f"Exported : {exported}")
    print(f"Skipped  : {skipped}")
    print(f"Database : {len(database)}")
    print("====================================")


if __name__ == "__main__":
    main()