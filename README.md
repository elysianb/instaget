# Instaget

Instagram command line tools for exporting saved collections and downloading media like images and videos.

## What this repo does

- List your saved Instagram collections
- Export all media links from a collection to a text file
- Download Instagram content from text file containing a list of Instagram URLs
- Flatten downloaded folders and clean empty directories

## Why use it

This project is built for quick, scriptable Instagram collection workflows:

- Export a collection as a clean text list
- Process Instagram URLs in bulk

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

## Quick start

### 1) List collections

```powershell
python .\instaget-savings.py --list --username YOUR_USERNAME --password YOUR_PASSWORD
```

### 2) Export one collection to a file

```powershell
python .\instaget-savings.py --get "Animals" .\animals.txt --username YOUR_USERNAME --password YOUR_PASSWORD
```

### 3) Download media from a file

```powershell
python .\instaget-content.py .\animals.txt
```

### 4) Flatten a directory tree

For each downloaded collection, the collection folder contains a subfolder per post. You can flatten it by using this command 

```powershell
python .\flatten_directory.py C:\path\to\folder\downloads\mycollection
```

## Project structure

```text
instaget/
├── instaget-savings.py
├── instaget-content.py
├── flatten_directory.py
├── requirements.txt
├── README.md
└── README.txt
```

## Notes

- The export script needs a valid Instagram session or valid credentials.
- Some downloads may require tools such as `ffmpeg`, `ffprobe`, `gallery-dl`, or `yt-dlp` depending on the content.
- On Windows, if `py` fails or points to the wrong interpreter, prefer the explicit Python executable path.

## License

This project is intended for personal automation and local usage. Respect Instagram terms of service and copyright rules when downloading or exporting content.
