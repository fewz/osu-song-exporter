# export_songs.py

import json
import shutil
import re
import sys

from pathlib import Path

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed
)

from threading import Lock

# =========================================================
# OPTIONAL DEPENDENCY
# =========================================================

try:

    from mutagen.id3 import (
        ID3,
        APIC,
        TPE1,
        TALB,
        error
    )

    from mutagen.flac import (
        FLAC,
        Picture
    )

    from mutagen.oggvorbis import OggVorbis

    from mutagen.mp4 import (
        MP4,
        MP4Cover
    )

    MUTAGEN_AVAILABLE = True

except:

    MUTAGEN_AVAILABLE = False

# =========================================================

CONFIG_FILE = "config.json"
DATABASE_FILE = "exported_songs.json"

db_lock = Lock()

# =========================================================
# LOAD CONFIG
# =========================================================

config_path = Path(CONFIG_FILE)

if not config_path.exists():

    print()
    print("======================================")
    print("ERROR: config.json not found")
    print("======================================")
    print()
    print("Please run:")
    print("config_ui.py")
    print()
    print("to create configuration first.")
    print()

    input("Press Enter to exit...")

    sys.exit(1)

try:

    with open(
        config_path,
        "r",
        encoding="utf-8"
    ) as f:

        config = json.load(f)

except Exception as e:

    print()
    print("======================================")
    print("ERROR: Failed to load config.json")
    print("======================================")
    print()
    print(e)
    print()

    input("Press Enter to exit...")

    sys.exit(1)

# =========================================================

SCRIPT_DIR = Path(__file__).parent

DATABASE_PATH = SCRIPT_DIR / DATABASE_FILE

# =========================================================
# HELPERS
# =========================================================


ARTIST_OVERWRITE_NONE = "none"
ARTIST_OVERWRITE_EMPTY = "empty"
ARTIST_OVERWRITE_ALL = "all"

ALBUM_OVERWRITE_NONE = "none"
ALBUM_OVERWRITE_EMPTY = "empty"
ALBUM_OVERWRITE_ALL = "all"

UNKNOWN_ALBUM = "Unknown Album"


def sanitize_filename(name):

    if not name:
        return "Unknown"

    name = re.sub(
        r'[<>:"/\\\\|?*]',
        '',
        name
    )

    name = name.strip()

    return name if name else "Unknown"


def generate_song_key(artist, title):

    return (
        f"{artist.lower()}::"
        f"{title.lower()}"
    )


def is_artist_empty(artist_value):

    if artist_value is None:
        return True

    if isinstance(artist_value, list):

        if not artist_value:
            return True

        artist_value = artist_value[0]

    text = str(artist_value).strip()

    if not text:
        return True

    if text.lower() in (
        "unknown",
        "?",
        "n/a",
        "na",
    ):
        return True

    return False


def get_existing_artist(audio_path):

    if not MUTAGEN_AVAILABLE:
        return None

    ext = audio_path.suffix.lower()

    try:

        if ext == ".mp3":

            try:
                tags = ID3(audio_path)
            except error:
                return None

            if "TPE1" in tags:
                return str(tags["TPE1"])

        elif ext == ".flac":

            audio = FLAC(audio_path)

            if "artist" in audio:
                return audio["artist"][0]

        elif ext == ".ogg":

            audio = OggVorbis(audio_path)

            if "artist" in audio:
                return audio["artist"][0]

        elif ext in [".m4a", ".mp4"]:

            audio = MP4(audio_path)

            if "\xa9ART" in audio:
                return audio["\xa9ART"][0]

    except Exception:
        return None

    return None


def is_album_empty(album_value):

    if album_value is None:
        return True

    if isinstance(album_value, list):

        if not album_value:
            return True

        album_value = album_value[0]

    text = str(album_value).strip()

    if not text:
        return True

    if text.lower() in (
        "unknown",
        "unknown album",
        "?",
        "n/a",
        "na",
    ):
        return True

    return False


def resolve_album(source):

    if source and str(source).strip():
        return str(source).strip()

    return UNKNOWN_ALBUM


def get_existing_album(audio_path):

    if not MUTAGEN_AVAILABLE:
        return None

    ext = audio_path.suffix.lower()

    try:

        if ext == ".mp3":

            try:
                tags = ID3(audio_path)
            except error:
                return None

            if "TALB" in tags:
                return str(tags["TALB"])

        elif ext == ".flac":

            audio = FLAC(audio_path)

            if "album" in audio:
                return audio["album"][0]

        elif ext == ".ogg":

            audio = OggVorbis(audio_path)

            if "album" in audio:
                return audio["album"][0]

        elif ext in [".m4a", ".mp4"]:

            audio = MP4(audio_path)

            if "\xa9alb" in audio:
                return audio["\xa9alb"][0]

    except Exception:
        return None

    return None


def should_embed_artist(overwrite_mode, audio_path):

    if overwrite_mode == ARTIST_OVERWRITE_NONE:
        return False

    if overwrite_mode == ARTIST_OVERWRITE_ALL:
        return True

    if overwrite_mode == ARTIST_OVERWRITE_EMPTY:
        return is_artist_empty(
            get_existing_artist(audio_path)
        )

    return False


def should_embed_album(overwrite_mode, audio_path):

    if overwrite_mode == ALBUM_OVERWRITE_NONE:
        return False

    if overwrite_mode == ALBUM_OVERWRITE_ALL:
        return True

    if overwrite_mode == ALBUM_OVERWRITE_EMPTY:
        return is_album_empty(
            get_existing_album(audio_path)
        )

    return False


# =========================================================
# DATABASE
# =========================================================


def load_database():

    if config["REFRESH_DATABASE"]:
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


# =========================================================
# PARSE OSU FILE
# =========================================================


def parse_osu_file(osu_file):

    encodings = [
        "utf-8",
        "utf-8-sig"
    ]

    for enc in encodings:

        try:

            title = None
            artist = None
            source = None
            audio = None
            background = None

            in_events = False

            with open(
                osu_file,
                "r",
                encoding=enc
            ) as f:

                for line in f:

                    line = line.strip()

                    # =============================
                    # TITLE
                    # =============================

                    if line.startswith(
                        "TitleUnicode:"
                    ):

                        value = line.replace(
                            "TitleUnicode:",
                            ""
                        ).strip()

                        if value:
                            title = value

                    elif (
                        line.startswith("Title:")
                        and not title
                    ):

                        title = line.replace(
                            "Title:",
                            ""
                        ).strip()

                    # =============================
                    # ARTIST
                    # =============================

                    if line.startswith(
                        "ArtistUnicode:"
                    ):

                        value = line.replace(
                            "ArtistUnicode:",
                            ""
                        ).strip()

                        if value:
                            artist = value

                    elif (
                        line.startswith("Artist:")
                        and not artist
                    ):

                        artist = line.replace(
                            "Artist:",
                            ""
                        ).strip()

                    # =============================
                    # SOURCE (ALBUM)
                    # =============================

                    elif line.startswith(
                        "Source:"
                    ):

                        value = line.replace(
                            "Source:",
                            ""
                        ).strip()

                        if value:
                            source = value

                    # =============================
                    # AUDIO
                    # =============================

                    elif line.startswith(
                        "AudioFilename:"
                    ):

                        audio = line.replace(
                            "AudioFilename:",
                            ""
                        ).strip()

                    # =============================
                    # EVENTS
                    # =============================

                    elif line.startswith(
                        "[Events]"
                    ):

                        in_events = True

                    elif (
                        line.startswith("[")
                        and line != "[Events]"
                    ):

                        in_events = False

                    elif (
                        in_events
                        and not background
                    ):

                        if line.startswith("0,0,"):

                            match = re.search(
                                r'"(.+?)"',
                                line
                            )

                            if match:

                                background = (
                                    match.group(1)
                                )

            if title and artist and audio:

                return {
                    "title": title,
                    "artist": artist,
                    "source": source,
                    "audio": audio,
                    "background": background
                }

        except:
            pass

    return None


# =========================================================
# EMBED COVER
# =========================================================


def embed_cover(
    audio_path,
    bg_path
):

    if not MUTAGEN_AVAILABLE:
        return

    try:

        ext = (
            audio_path.suffix
            .lower()
        )

        bg_ext = (
            bg_path.suffix
            .lower()
        )

        mime = "image/jpeg"

        if bg_ext == ".png":
            mime = "image/png"

        with open(bg_path, "rb") as img:

            image_data = img.read()

        # =================================================
        # MP3
        # =================================================

        if ext == ".mp3":

            try:
                tags = ID3(audio_path)

            except error:
                tags = ID3()

            tags.delall("APIC")

            tags.add(
                APIC(
                    encoding=3,
                    mime=mime,
                    type=3,
                    desc="Cover",
                    data=image_data
                )
            )

            tags.save(audio_path)

        # =================================================
        # FLAC
        # =================================================

        elif ext == ".flac":

            audio = FLAC(audio_path)

            audio.clear_pictures()

            pic = Picture()

            pic.data = image_data
            pic.type = 3
            pic.mime = mime
            pic.desc = "Cover"

            audio.add_picture(pic)

            audio.save()

        # =================================================
        # OGG
        # =================================================

        elif ext == ".ogg":

            import base64

            audio = OggVorbis(audio_path)

            encoded = base64.b64encode(
                image_data
            ).decode("ascii")

            audio["metadata_block_picture"] = [
                encoded
            ]

            audio.save()

        # =================================================
        # M4A / MP4
        # =================================================

        elif ext in [
            ".m4a",
            ".mp4"
        ]:

            audio = MP4(audio_path)

            cover_format = (
                MP4Cover.FORMAT_JPEG
            )

            if bg_ext == ".png":

                cover_format = (
                    MP4Cover.FORMAT_PNG
                )

            audio["covr"] = [
                MP4Cover(
                    image_data,
                    imageformat=cover_format
                )
            ]

            audio.save()

        print(
            f"[COVER] Embedded:"
            f" {audio_path.name}"
        )

    except Exception as e:

        print(
            f"[WARNING] Cover embed failed:"
            f" {audio_path.name}"
        )

        print(e)


# =========================================================
# EMBED ARTIST
# =========================================================


def embed_artist(
    audio_path,
    artist
):

    if not MUTAGEN_AVAILABLE:
        return False

    if is_artist_empty(artist):
        return False

    overwrite_mode = config.get(
        "ARTIST_OVERWRITE",
        ARTIST_OVERWRITE_EMPTY
    )

    if not should_embed_artist(
        overwrite_mode,
        audio_path
    ):
        return False

    try:

        ext = (
            audio_path.suffix
            .lower()
        )

        # =================================================
        # MP3
        # =================================================

        if ext == ".mp3":

            try:
                tags = ID3(audio_path)

            except error:
                tags = ID3()

            tags.delall("TPE1")

            tags.add(
                TPE1(
                    encoding=3,
                    text=artist
                )
            )

            tags.save(audio_path)

        # =================================================
        # FLAC
        # =================================================

        elif ext == ".flac":

            audio = FLAC(audio_path)

            audio["artist"] = artist

            audio.save()

        # =================================================
        # OGG
        # =================================================

        elif ext == ".ogg":

            audio = OggVorbis(audio_path)

            audio["artist"] = artist

            audio.save()

        # =================================================
        # M4A / MP4
        # =================================================

        elif ext in [
            ".m4a",
            ".mp4"
        ]:

            audio = MP4(audio_path)

            audio["\xa9ART"] = artist

            audio.save()

        else:
            return False

        print(
            f"[ARTIST] Embedded:"
            f" {audio_path.name}"
        )

        return True

    except Exception as e:

        print(
            f"[WARNING] Artist embed failed:"
            f" {audio_path.name}"
        )

        print(e)

        return False


# =========================================================
# EMBED ALBUM
# =========================================================


def embed_album(
    audio_path,
    album
):

    if not MUTAGEN_AVAILABLE:
        return False

    if is_album_empty(album):
        album = UNKNOWN_ALBUM

    overwrite_mode = config.get(
        "ALBUM_OVERWRITE",
        ALBUM_OVERWRITE_EMPTY
    )

    if not should_embed_album(
        overwrite_mode,
        audio_path
    ):
        return False

    try:

        ext = (
            audio_path.suffix
            .lower()
        )

        # =================================================
        # MP3
        # =================================================

        if ext == ".mp3":

            try:
                tags = ID3(audio_path)

            except error:
                tags = ID3()

            tags.delall("TALB")

            tags.add(
                TALB(
                    encoding=3,
                    text=album
                )
            )

            tags.save(audio_path)

        # =================================================
        # FLAC
        # =================================================

        elif ext == ".flac":

            audio = FLAC(audio_path)

            audio["album"] = album

            audio.save()

        # =================================================
        # OGG
        # =================================================

        elif ext == ".ogg":

            audio = OggVorbis(audio_path)

            audio["album"] = album

            audio.save()

        # =================================================
        # M4A / MP4
        # =================================================

        elif ext in [
            ".m4a",
            ".mp4"
        ]:

            audio = MP4(audio_path)

            audio["\xa9alb"] = album

            audio.save()

        else:
            return False

        print(
            f"[ALBUM] Embedded:"
            f" {audio_path.name}"
        )

        return True

    except Exception as e:

        print(
            f"[WARNING] Album embed failed:"
            f" {audio_path.name}"
        )

        print(e)

        return False


# =========================================================
# PROCESS SONG
# =========================================================


def process_folder(
    folder,
    database,
    export_root
):

    try:

        osu_files = list(
            folder.glob("*.osu")
        )

        if not osu_files:
            return None

        metadata = None

        for osu_file in osu_files:

            metadata = parse_osu_file(
                osu_file
            )

            if metadata:
                break

        if not metadata:
            return None

        title = metadata["title"]
        artist = metadata["artist"]

        song_key = generate_song_key(
            artist,
            title
        )

        with db_lock:

            if song_key in database:

                return {
                    "status": "skip",
                    "artist": artist,
                    "title": title
                }

        audio_file = (
            folder /
            metadata["audio"]
        )

        if not audio_file.exists():
            return None

        safe_artist = sanitize_filename(
            artist
        )

        safe_title = sanitize_filename(
            title
        )

        artist_folder = (
            export_root /
            safe_artist
        )

        artist_folder.mkdir(
            parents=True,
            exist_ok=True
        )

        ext = audio_file.suffix

        output_audio = (
            artist_folder /
            f"{safe_title}{ext}"
        )

        counter = 1

        while output_audio.exists():

            output_audio = (
                artist_folder /
                f"{safe_title} ({counter}){ext}"
            )

            counter += 1

        # =================================================
        # COPY / MOVE
        # =================================================

        if config["COPY_MODE"]:

            shutil.copy2(
                audio_file,
                output_audio
            )

        else:

            shutil.move(
                audio_file,
                output_audio
            )

        # =================================================
        # BACKGROUND EXPORT
        # =================================================

        if (
            config["EXPORT_BACKGROUND"]
            and metadata["background"]
        ):

            bg_file = (
                folder /
                metadata["background"]
            )

            if bg_file.exists():
                # =========================================
                # EMBED COVER
                # =========================================

                embed_cover(
                    output_audio,
                    bg_file
                )

        # =================================================
        # EMBED ARTIST
        # =================================================

        embed_artist(
            output_audio,
            artist
        )

        # =================================================
        # EMBED ALBUM
        # =================================================

        album = resolve_album(
            metadata.get("source")
        )

        embed_album(
            output_audio,
            album
        )

        # =================================================
        # SAVE DATABASE
        # =================================================

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


# =========================================================
# PLAYLIST
# =========================================================


def generate_playlist(
    database,
    export_root
):

    global_playlist = (
        export_root /
        "playlist.m3u"
    )

    with open(
        global_playlist,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("#EXTM3U\n")

        for item in database.values():

            audio_path = Path(
                item["audio"]
            )

            if audio_path.exists():

                rel = (
                    audio_path.relative_to(
                        export_root
                    )
                )

                f.write(
                    str(rel) + "\n"
                )

    # =====================================================
    # ARTIST PLAYLIST
    # =====================================================

    artist_map = {}

    for item in database.values():

        artist_map.setdefault(
            item["artist"],
            []
        ).append(item)

    for artist, songs in artist_map.items():

        safe_artist = sanitize_filename(
            artist
        )

        artist_folder = (
            export_root /
            safe_artist
        )

        playlist = (
            artist_folder /
            "playlist.m3u"
        )

        with open(
            playlist,
            "w",
            encoding="utf-8"
        ) as f:

            f.write("#EXTM3U\n")

            for song in songs:

                audio_path = Path(
                    song["audio"]
                )

                if audio_path.exists():

                    f.write(
                        audio_path.name
                        + "\n"
                    )


# =========================================================
# MAIN
# =========================================================


def main():

    export_root = Path(
        config["EXPORT_FOLDER"]
    )

    export_root.mkdir(
        parents=True,
        exist_ok=True
    )

    database = load_database()

    songs_path = Path(
        config["OSU_SONGS_FOLDER"]
    )

    folders = [

        f for f in songs_path.iterdir()

        if f.is_dir()
    ]

    if not config["LIMIT_ALL"]:

        folders = folders[
            :config["LIMIT"]
        ]

    print(
        f"Folder scan : {len(folders)}"
    )

    print(
        f"Database    : {len(database)}"
    )

    print(
        f"Workers     : "
        f"{config['MAX_WORKERS']}"
    )

    print()

    if not MUTAGEN_AVAILABLE:

        print(
            "[WARNING] mutagen not installed"
        )

        print(
            "Cover / metadata embedding disabled"
        )

        print(
            "Install using:"
        )

        print(
            "pip install mutagen"
        )

        print()

    exported = 0
    skipped = 0

    with ThreadPoolExecutor(
        max_workers=config["MAX_WORKERS"]
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

        for future in as_completed(
            futures
        ):

            result = future.result()

            if not result:
                continue

            if result["status"] == "skip":

                skipped += 1

                print(
                    f"[SKIP] "
                    f"{result['artist']} - "
                    f"{result['title']}"
                )

            elif (
                result["status"]
                == "export"
            ):

                exported += 1

                print(
                    f"[EXPORT] "
                    f"{result['artist']} - "
                    f"{result['title']}"
                )

    save_database(database)

    if config["GENERATE_PLAYLIST"]:

        generate_playlist(
            database,
            export_root
        )

    print()
    print(
        "======================================"
    )

    print(
        f"Exported : {exported}"
    )

    print(
        f"Skipped  : {skipped}"
    )

    print(
        f"Database : {len(database)}"
    )

    print(
        "======================================"
    )

    print()

    input(
        "Press Enter to exit..."
    )


if __name__ == "__main__":
    main()