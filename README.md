# osu! Song Exporter

Export all songs from your osu! Songs folder into a clean music library organized by artist.

Supports:
- Unicode title & artist
- Artist & album tag embedding
- Incremental export
- Playlist generation
- Cover/background export
- Multithread processing
- Persistent JSON database
- Duplicate prevention
- GUI configuration editor

---

# Features

- Export all osu! songs automatically
- Organize songs by artist folder
- Unicode metadata support (`TitleUnicode`, `ArtistUnicode`)
- Embed artist tags from beatmap metadata
- Embed album tags from beatmap `Source` (fallback: `Unknown Album`)
- Configurable artist / album overwrite modes (`none`, `empty`, `all`)
- Export beatmap background / cover image
- Generate global playlist (`playlist.m3u`)
- Generate playlist per artist
- Incremental export system
- Skip previously exported songs
- Persistent JSON database
- Multithread processing
- Copy mode or move mode
- GUI configuration editor
- Scrollable configuration UI
- Config validation system
- Testing limit support

---

# Project Structure

```text
project_folder
├── config_ui.py
├── export_songs.py
├── config.json
├── exported_songs.json
```

---

# Requirements

- Python 3.9+
- [mutagen](https://mutagen.readthedocs.io/) (optional, recommended for cover / artist / album embedding)

```bash
pip install mutagen
```

---

# Configuration UI

The project includes a dedicated graphical configuration editor.

Launch configuration UI:

```bash
python config_ui.py
```

The UI supports:

- osu! Songs folder picker
- Export folder picker
- Export all songs checkbox
- Song limit input
- Copy / move mode
- Export background toggle
- Artist tag overwrite mode (combobox)
- Album tag overwrite mode (combobox)
- Playlist generation toggle
- Refresh database toggle
- Max worker configuration
- Scrollable interface
- Automatic config validation

---

# Default Configuration

| Setting | Default |
|---|---|
| Copy Mode | True |
| Export Background | True |
| Generate Playlist | False |
| Refresh Database | False |
| Export All Songs | True |
| Max Workers | 8 |
| Artist Overwrite | `empty` |
| Album Overwrite | `empty` |

---

# Configuration File Example

Generated automatically after saving:

```json
{
    "OSU_SONGS_FOLDER": "D:\\Games\\osu!\\Songs",
    "EXPORT_FOLDER": "D:\\Exported_Osu",
    "LIMIT_ALL": true,
    "LIMIT": 10,
    "COPY_MODE": true,
    "EXPORT_BACKGROUND": true,
    "GENERATE_PLAYLIST": false,
    "REFRESH_DATABASE": false,
    "MAX_WORKERS": 8,
    "ARTIST_OVERWRITE": "empty",
    "ALBUM_OVERWRITE": "empty"
}
```

### Artist / Album Overwrite Modes

| Value | Behavior |
|---|---|
| `none` | Do not write tags |
| `empty` | Write only when the file tag is missing or unknown |
| `all` | Always overwrite with beatmap metadata |

---

---

# Export Songs

After saving configuration:

```bash
python export_songs.py
```

The exporter will:

1. Scan all osu! beatmap folders
2. Read metadata from `.osu` files
3. Extract:
   - Artist (`ArtistUnicode` / `Artist`)
   - Title (`TitleUnicode` / `Title`)
   - Source (used as album)
   - Audio file
   - Background image
4. Export songs into artist folders
5. Embed cover, artist, and album tags (when mutagen is installed)
6. Save export history into JSON database
7. Generate playlists automatically (if enabled)

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

# Incremental Export System

The exporter stores exported songs in:

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

Enable:

```json
"REFRESH_DATABASE": true
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

```json
"MAX_WORKERS": 16
```

Higher worker count significantly improves export speed on large libraries.

---

# Unicode Support

The exporter automatically prioritizes:

- `TitleUnicode`
- `ArtistUnicode`

Example:

```text
YOASOBI - アイドル
```

---

# Metadata Embedding

When **mutagen** is installed, exported audio files can receive embedded tags.

## Artist

- Taken from `ArtistUnicode`, falling back to `Artist`
- Controlled by `ARTIST_OVERWRITE` (`none` / `empty` / `all`)

## Album

- Taken from beatmap `Source`
- If `Source` is empty, uses **`Unknown Album`**
- Controlled by `ALBUM_OVERWRITE` (`none` / `empty` / `all`)

Supported formats for tag embedding: `.mp3`, `.flac`, `.ogg`, `.m4a`, `.mp4`

---

# Missing Config Protection

If `config.json` does not exist:

```text
======================================
ERROR: config.json not found
======================================

Please run:
config_ui.py

to create configuration first.
```

---

# Notes

- Duplicate difficulty maps are skipped automatically
- Windows filename sanitization included
- Background export is optional
- Artist / album embedding requires mutagen
- JSON database stored beside Python script
- Supports copy mode and move mode
- Fully standalone project (mutagen optional)

---

# License

MIT License