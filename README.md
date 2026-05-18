# osu! Song Exporter

Export all songs from your osu! Songs folder into a clean music library organized by artist.

Supports:
- Unicode title & artist
- Incremental export
- Playlist generation
- Cover/background export
- Multithread processing
- Persistent JSON database
- Duplicate prevention

---

# Features

- Export all osu! songs automatically
- Organize songs by artist folder
- Unicode metadata support (`TitleUnicode`, `ArtistUnicode`)
- Export beatmap background / cover image
- Generate global playlist (`playlist.m3u`)
- Generate playlist per artist
- Incremental export system
- Skip previously exported songs
- Persistent JSON database
- Multithread processing
- Copy mode or move mode
- Testing limit support

---

# Example Output

```text
D:\Exported_Osu
├── playlist.m3u
│
├── YOASOBI
│   ├── playlist.m3u
│   ├── アイドル.mp3
│   ├── アイドル_cover.jpg
│
├── Camellia
│   ├── playlist.m3u
│   ├── GHOST.ogg
│   ├── GHOST_cover.jpg
```

---

# Project Structure

```text
project_folder
├── main.py
├── config.py
├── exported_songs.json
```

---

# Requirements

- Python 3.9+
- No external libraries required

---

# Installation

Clone repository:

```bash
git clone https://github.com/yourname/osu-song-exporter.git
```

Open project folder:

```bash
cd osu-song-exporter
```

Run:

```bash
python main.py
```

---

# Configuration

Edit:

```text
config.py
```

Example:

```python
# osu Songs folder
OSU_SONGS_FOLDER = r"D:\Games\osu!\Songs"

# Export output folder
EXPORT_FOLDER = r"D:\Exported_Osu"

# True = copy
# False = move
COPY_MODE = True

# Export background image
EXPORT_BACKGROUND = True

# Generate playlists
GENERATE_PLAYLIST = True

# Rebuild database
REFRESH_DATABASE = False

# None = export all songs
LIMIT = 10

# Multithread workers
MAX_WORKERS = 8
```

---

# Incremental Export System

The script stores exported songs in:

```text
exported_songs.json
```

Duplicate detection uses:

```text
unicode_artist + unicode_title
```

Example:

```json
{
    "yoasobi::アイドル": {
        "artist": "YOASOBI",
        "title": "アイドル",
        "audio": "D:\\Exported_Osu\\YOASOBI\\アイドル.mp3"
    }
}
```

---

# Refresh Database

To rebuild database and export everything again:

```python
REFRESH_DATABASE = True
```

| Value | Behavior |
|---|---|
| False | Incremental export |
| True | Full rebuild and re-export |

---

# Playlist Generation

Generated automatically:

- Global playlist
- Playlist per artist

Format:

```text
playlist.m3u
```

Compatible with:
- VLC
- foobar2000
- MusicBee
- AIMP
- Poweramp

---

# Supported Audio Formats

- `.mp3`
- `.ogg`
- `.wav`
- `.flac`

---

# Performance Tips

For SSD and multicore CPUs:

```python
MAX_WORKERS = 16
```

Higher worker count significantly improves export speed on large libraries.

---

# Unicode Support

The script automatically prioritizes:

- `TitleUnicode`
- `ArtistUnicode`

Example:

```text
YOASOBI - アイドル
```

---

# Notes

- Duplicate difficulty maps are skipped automatically
- Windows filename sanitization included
- Background export is optional
- JSON database stored beside Python script
- Supports copy mode and move mode

---

# License

MIT License