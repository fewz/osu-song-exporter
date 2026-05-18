# config.py

# =========================================================
# PATH
# =========================================================

# Folder Songs osu!
OSU_SONGS_FOLDER = r"F:\Game\osu!\Songs"

# Folder output export
EXPORT_FOLDER = r"F:\Music"

# =========================================================
# EXPORT
# =========================================================

# True  = copy
# False = move
COPY_MODE = True

# Export background / cover
EXPORT_BACKGROUND = True

# Generate playlist
GENERATE_PLAYLIST = True

# =========================================================
# DATABASE
# =========================================================

# True  = rebuild database
# False = incremental export
REFRESH_DATABASE = False

# =========================================================
# PERFORMANCE
# =========================================================

# None = semua lagu
LIMIT = None

# Multithread
MAX_WORKERS = 8