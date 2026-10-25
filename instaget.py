"""Instagram content downloader.

This script reads a text file containing Instagram URLs, detects whether each item is
 a reel or a regular post/carousel, and downloads it using the appropriate external tool.

Usage examples:
  py instaget.py links.txt
  py instaget.py C:/temp/links.txt

The downloader expects a file with one URL per line and uses gallery-dl for posts and
 yt-dlp for reels. FFmpeg and FFprobe must be installed and available on PATH.
"""

import os
import re
import sys
import json
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LINKS_FILE = None
DOWNLOAD_DIR = None
LOG_FILE = None

BROWSER = "firefox"

# Maximum number of characters for the description
DESCRIPTION_MAX = 40


# ============================================================
# GENERAL TOOLS
# ============================================================

def resolve_links_file(raw_path):
    """Resolve a relative or absolute path to the links file."""

    if not raw_path:
        return None

    candidate = Path(raw_path)

    if candidate.is_absolute():
        return candidate.resolve()

    # Relative path from the current working directory
    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    # Relative path from the script directory
    script_candidate = (BASE_DIR / candidate).resolve()
    if script_candidate.exists():
        return script_candidate

    # If the file does not exist yet, return the most logical resolution.
    return cwd_candidate


def configure_paths(raw_path):
    """Initialize the working paths from the provided file."""

    global LINKS_FILE, DOWNLOAD_DIR, LOG_FILE

    links_file = resolve_links_file(raw_path)
    if links_file is None:
        return

    links_file = links_file.resolve()

    stem = links_file.stem
    LINKS_FILE = links_file
    DOWNLOAD_DIR = BASE_DIR / "downloads" / stem
    LOG_FILE = BASE_DIR / f"report-{stem}.txt"

    return links_file


def build_arg_parser():
    """Create the CLI parser for the content downloader."""

    parser = argparse.ArgumentParser(
        description=(
            "Instagram content downloader for reels, posts, photos, videos, and carousels. "
            "This tool reads a text file containing Instagram URLs and downloads each item "
            "into a per-post folder under the repository's downloads directory."
        ),
        epilog=(
            "Examples:\n"
            "  py instaget.py links.txt\n"
            "  py instaget.py ./links/my-collection.txt\n"
            "  py instaget.py C:/temp/links.txt\n\n"
            "Behavior:\n"
            "  * Each non-comment line in the input file is treated as an Instagram URL.\n"
            "  * Reels are downloaded with yt-dlp.\n"
            "  * Posts, photos, carousels and other gallery items are downloaded with gallery-dl.\n"
            "  * FFmpeg/FFprobe must be installed and available on PATH for video normalization.\n"
            "  * A report file is created next to the script for each processed collection."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "collection_file",
        nargs="?",
        help=(
            "Relative or absolute path of the links file to process.\n"
            "Examples:\n"
            "  ./links/sample3.txt\n"
            "  ../other-folder/sample3.txt\n"
            "  C:/path/to/sample3.txt"
        ),
    )
    return parser


def log(message):
    """Print the message and write it to the report file."""

    print(message)

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as f:

        f.write(message + "\n")


def extract_instagram_id(url):
    """Extract the Instagram identifier."""

    match = re.search(
        r"instagram\.com/(?:p|reel|tv)/([^/?#]+)",
        url,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def is_instagram_url(url):
    """Check whether the URL is a supported Instagram URL."""

    return bool(
        re.search(
            r"https?://(?:www\.)?instagram\.com/(?:p|reel|tv)/",
            url,
            re.IGNORECASE,
        )
    )


def is_reel(url):
    """Determine whether the URL is a Reel."""

    return bool(
        re.search(
            r"instagram\.com/reel/",
            url,
            re.IGNORECASE,
        )
    )


def clean_filename_part(text, max_length=None):
    r"""
    Clean a Windows filename segment.

    Removes, notably:
    < > : " / \ | ? *
    """

    if text is None:
        text = ""

    text = str(text)

    # Line breaks
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    # Windows-invalid characters
    text = re.sub(
        r'[<>:"/\\|?*]',
        "",
        text,
    )

    # Control characters
    text = re.sub(
        r"[\x00-\x1f\x7f]",
        "",
        text,
    )

    # Multiple spaces
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    text = text.strip()

    # Spaces to dashes
    text = re.sub(
        r"\s+",
        "-",
        text,
    )

    # Multiple dashes to a single dash
    text = re.sub(
        r"-{2,}",
        "-",
        text,
    )

    # Trim beginning and end
    text = text.strip(".-")

    if max_length is not None:

        text = text[:max_length]

        text = text.rstrip(".-")

    return text


def shorten_description(description):
    """Limit the description to 40 characters."""

    if not description:
        return "no-description"

    description = clean_filename_part(
        description,
        DESCRIPTION_MAX,
    )

    if not description:
        return "no-description"

    return description


def run_command(command):
    """Execute an external command."""

    print()
    print("-" * 70)
    print("Command:")

    display_command = []

    for item in command:

        item = str(item)

        if " " in item:
            display_command.append(
                f'"{item}"'
            )
        else:
            display_command.append(
                item
            )

    print(
        " ".join(display_command)
    )

    result = subprocess.run(
        command
    )

    return result.returncode == 0


# ============================================================
# FFMPEG CHECK
# ============================================================

def check_ffmpeg():
    """Check whether FFmpeg is available."""

    try:

        result = subprocess.run(
            [
                "ffmpeg",
                "-version",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return result.returncode == 0

    except FileNotFoundError:

        return False


def check_ffprobe():
    """Check whether FFprobe is available."""

    try:

        result = subprocess.run(
            [
                "ffprobe",
                "-version",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        return result.returncode == 0

    except FileNotFoundError:

        return False


# ============================================================
# VIDEO CODEC DETECTION
# ============================================================

def get_video_codec(video_file):
    """
    Return the main video codec.

    Example:
        h264
        vp9
        av1
    """

    command = [
        "ffprobe",

        "-v",
        "error",

        "-select_streams",
        "v:0",

        "-show_entries",
        "stream=codec_name",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(video_file),
    ]

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        codec = result.stdout.strip()

        if codec:
            return codec.lower()

    except Exception:
        pass

    return None


# ============================================================
# WINDOWS VIDEO NORMALIZATION
# ============================================================

def normalize_video_for_windows(video_file):
    """
    Prepare a video for Windows 11.

    H.264:
        remux without re-encoding

    Other codecs:
        H.264 + AAC conversion

    The original file keeps exactly its name.
    """

    if not video_file.exists():

        return False

    log("")
    log(
        f"Video processing: {video_file.name}"
    )

    codec = get_video_codec(
        video_file
    )

    log(
        f"Detected codec: "
        f"{codec or 'unknown'}"
    )

    normalized_file = video_file.with_name(
        video_file.stem
        + ".windows.mp4"
    )

    if normalized_file.exists():

        try:
            normalized_file.unlink()
        except Exception:
            pass

    if codec in (
        "h264",
        "avc1",
    ):

        log(
            "H.264 detected."
        )

        log(
            "Remux without re-encoding."
        )

        command = [
            "ffmpeg",

            "-y",

            "-i",
            str(video_file),

            "-map",
            "0",

            "-c",
            "copy",

            "-movflags",
            "+faststart",

            str(normalized_file),
        ]

    else:

        log(
            "Codec not ideal for Windows."
        )

        log(
            "Converting to H.264 + AAC..."
        )

        command = [
            "ffmpeg",

            "-y",

            "-i",
            str(video_file),

            "-map",
            "0:v:0",

            "-map",
            "0:a?",

            "-c:v",
            "libx264",

            "-preset",
            "medium",

            "-crf",
            "18",

            "-pix_fmt",
            "yuv420p",

            "-c:a",
            "aac",

            "-b:a",
            "192k",

            "-movflags",
            "+faststart",

            str(normalized_file),
        ]

    success = run_command(command)

    if not success:
        return False

    return True


def process_videos_in_folder(output_dir, post_id):
    """Process MP4 files inside a post folder."""

    files = sorted(output_dir.glob("*.mp4"))

    if not files:
        return True

    total = len(files)
    log(
        f"Processing {total} video file(s) for post {post_id}."
    )

    for video_file in files:

        normalized = normalize_video_for_windows(video_file)

        if not normalized:
            log(
                f"Normalization failed for {video_file.name}"
            )
            return False

    return True


# ============================================================
# GALLERY-DL
# ============================================================

def download_gallery(url, post_id):
    """
    Download posts, photos, videos, and carousels
    with gallery-dl.

    Then ALL MP4 files in the folder are processed by FFmpeg.
    """

    output_dir = DOWNLOAD_DIR / post_id

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    filename_format = (
        "{date:%Y%m%d-%H%M%S}-"
        "{username}-"
        "{post_shortcode}-"
        "{description[:40]}-"
        "{num:02}."
        "{extension}"
    )

    command = [
        "gallery-dl",

        "--cookies-from-browser",
        BROWSER,

        "--no-skip",

        "--restrict-filenames",
        "windows",

        "-f",
        filename_format,

        "-D",
        str(output_dir),

        url,
    ]

    success = run_command(
        command
    )

    if not success:

        return False

    process_videos_in_folder(
        output_dir,
        post_id,
    )

    return True


# ============================================================
# VIDEO METADATA
# ============================================================

def get_video_metadata(url):
    """Retrieve metadata for a Reel with yt-dlp."""

    command = [
        "yt-dlp",

        "--cookies-from-browser",
        BROWSER,

        "--dump-single-json",

        "--no-download",

        url,
    ]

    print()
    print("-" * 70)
    print(
        "Retrieving video metadata..."
    )
    print("-" * 70)

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    except Exception as e:

        log(
            f"Metadata error: {e}"
        )

        return None

    if result.returncode != 0:

        print(
            result.stderr
        )

        log(
            "Unable to retrieve "
            "metadata."
        )

        return None

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        log("Metadata response is not valid JSON.")
        return None

    return data


def download_video(url, post_id):
    """Download a Reel or single video with yt-dlp."""

    output_dir = DOWNLOAD_DIR / post_id
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "yt-dlp",

        "--cookies-from-browser",
        BROWSER,

        "-o",
        str(output_dir / "%(title)s.%(ext)s"),

        url,
    ]

    success = run_command(command)

    if not success:
        return False

    return process_videos_in_folder(output_dir, post_id)


def process_url(url, number, total):
    """Process a single Instagram URL."""

    print()
    print("-" * 70)
    print(f"Processing {number}/{total}: {url}")
    print("-" * 70)

    post_id = extract_instagram_id(url)

    if not post_id:
        print("Invalid Instagram URL.")
        return False

    log(
        "=" * 70
    )
    log(
        f"URL: {url}"
    )
    log(
        f"ID: {post_id}"
    )
    log("=" * 70)

    if is_reel(url):

        log(
            "Type detected: REEL / VIDEO"
        )

        log(
            "Downloading with yt-dlp..."
        )

        success = download_video(
            url,
            post_id,
        )

        if success:

            log(
                f"OK - video: {post_id}"
            )

            return True

        log(
            f"VIDEO FAILED: {post_id}"
        )

        return False

    log(
        "Type detected: "
        "POST / PHOTO / VIDEO / CAROUSEL"
    )

    log(
        "Downloading with gallery-dl..."
    )

    success = download_gallery(
        url,
        post_id,
    )

    if success:

        log(
            f"OK - gallery-dl: {post_id}"
        )

        return True

    log(
        f"gallery-dl failed: "
        f"{post_id}"
    )

    log(
        "Retrying with yt-dlp..."
    )

    success = download_video(
        url,
        post_id,
    )

    if success:

        log(
            f"OK - fallback yt-dlp: "
            f"{post_id}"
        )

        return True

    log(
        f"FAILED: {post_id}"
    )

    return False


# ============================================================
# MAIN
# ============================================================

def main():

    parser = build_arg_parser()
    args = parser.parse_args()

    if not args.collection_file:
        parser.print_help()
        return 0

    configure_paths(args.collection_file)

    if LINKS_FILE is None or DOWNLOAD_DIR is None or LOG_FILE is None:
        parser.print_help()
        sys.exit(1)

    print()
    print("=" * 70)
    print("          INSTAGRAM DOWNLOADER V5")
    print("=" * 70)
    print()

    print(
        f"Folder : {BASE_DIR}"
    )

    print(
        f"Links  : {LINKS_FILE}"
    )

    print(
        f"Output : {DOWNLOAD_DIR}"
    )

    print()

    if not check_ffmpeg():

        print()
        print(
            "ERROR: FFmpeg was not found."
        )

        print()

        sys.exit(1)

    print(
        "FFmpeg: OK"
    )

    if not check_ffprobe():

        print()
        print(
            "ERROR: FFprobe was not found."
        )

        print()

        sys.exit(1)

    print(
        "FFprobe: OK"
    )

    if not LINKS_FILE.exists():

        print()
        print(
            "ERROR: link file not found."
        )

        print()

        print(
            f"Expected file: "
            f"{LINKS_FILE}"
        )

        print()

        sys.exit(1)

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        LINKS_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        urls = [
            line.strip()
            for line in f
            if line.strip()
            and not line.strip().startswith("#")
        ]

    urls = list(
        dict.fromkeys(urls)
    )

    instagram_urls = [
        url
        for url in urls
        if is_instagram_url(url)
    ]

    if not instagram_urls:

        print()
        print(
            "No valid Instagram URL found."
        )

        print()

        sys.exit(1)

    with open(
        LOG_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "INSTAGRAM DOWNLOAD REPORT "
            "V5\n"
        )

        f.write(
            f"Date: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        )

        f.write(
            f"Number of URLs: "
            f"{len(instagram_urls)}\n"
        )

        f.write("\n")

    log(
        f"{len(instagram_urls)} "
        f"URL(s) to process."
    )

    success = 0
    failed = 0

    for number, url in enumerate(
        instagram_urls,
        start=1,
    ):

        try:

            result = process_url(
                url,
                number,
                len(instagram_urls),
            )

            if result:

                success += 1

            else:

                failed += 1

        except KeyboardInterrupt:

            log("")
            log(
                "USER STOP REQUESTED."
            )

            break

        except Exception as e:

            failed += 1

            log(
                f"UNEXPECTED ERROR: "
                f"{type(e).__name__}: {e}"
            )

    log("")
    log("=" * 70)
    log("SUMMARY")
    log("=" * 70)

    log(
        f"Processed URLs: "
        f"{success + failed}"
    )

    log(
        f"Successes     : "
        f"{success}"
    )

    log(
        f"Failures      : "
        f"{failed}"
    )

    log(
        f"Folder        : "
        f"{DOWNLOAD_DIR}"
    )

    log(
        f"Report        : "
        f"{LOG_FILE}"
    )

    log("=" * 70)

    log(
        "End of processing."
    )


if __name__ == "__main__":
    main()
