# Instaget

Instagram command line tools for exporting saved collections and downloading media like images and videos.

For quick, scriptable Instagram collection workflows:

- Export a collection as a clean text list
- Process Instagram URLs in bulk from a clean text list

## Quick start

### 1) List collections

List your saved Instagram collections using the session already open in Firefox:

```powershell
python .\instaget-savings.py --list --firefox-cookies
```

Firefox must be logged in to Instagram. The script reads the session cookie locally.


Alternatively, you can authenticate with your Instagram credentials:

```powershell
python .\instaget-savings.py --list --username YOUR_USERNAME --password YOUR_PASSWORD
```

### 2) Export one collection to a file

Export all media links from a collection to a text file, using Firefox's session:

```powershell
python .\instaget-savings.py --get "Animals" .\animals.txt --firefox-cookies
```

Alternatively, you can authenticate with your Instagram credentials:

```powershell
python .\instaget-savings.py --get "Animals" .\animals.txt --username YOUR_USERNAME --password YOUR_PASSWORD
```

### 3) Download media from a file

Download Instagram content from text file containing a list of Instagram URLs

ATTENTION : 
- you need to install Firefox, because instaget use your instagram session from Firefox
- instagram has a rate limit. So, downloads are limited by days (around 1_000 downloads per days). When download doesn't work. Stop and restart two days after.

```powershell
python .\instaget.py .\animals.txt
```

### 4) Flatten a directory tree

For each downloaded collection, the collection folder contains a subfolder per post. You can flatten it by using this command 

```powershell
python .\flatten_directory.py C:\path\to\folder\downloads\mycollection
```

## Requirements

- Python 3.12+
- Dependencies from `requirements.txt`
- ffmpeg

Install dependencies:

```powershell
python -m pip install -r .\requirements.txt
```

If `python` does not resolve correctly on your machine, use the full interpreter path, for example:

```powershell
& $env:userprofile\AppData\Local\Programs\Python\Python312\python.exe -m pip install -r .\requirements.txt
```

## Notes

- `instaget-savings.py --firefox-cookies` uses the Instagram session cookie stored by Firefox. Firefox must be logged in to Instagram.
- The export script can also authenticate with `--username` and `--password`, or reuse a saved session file specified with `--session`.
- `instaget.py` uses Firefox cookies through `gallery-dl` and `yt-dlp` when downloading media.
- Some downloads may require tools such as `ffmpeg`, `ffprobe`, `gallery-dl`, or `yt-dlp` depending on the content.
- On Windows, if `py` fails or points to the wrong interpreter, prefer the explicit Python executable path.

## License

This project is intended for personal automation and local usage. Respect Instagram terms of service and copyright rules when downloading or exporting content.
