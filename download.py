import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
MAIN_REPO = "aseprite/aseprite"
MAIN_REPO_DIR = SRC_DIR / "aseprite"
SKIA_DIR = SRC_DIR / "skia"
SKIA_ZIP_PATH = SRC_DIR / "Skia-Windows-Release-x64.zip"
VERSION_FILE = ROOT_DIR / "version.txt"

def download_json(url: str):
    request = urllib.request.Request(url,headers={"Accept": "application/vnd.github+json","User-Agent": "aseprite-auto-build",},)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)

def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "aseprite-auto-build",
        },
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        with destination.open("wb") as output_file:
            shutil.copyfileobj(response, output_file)

def get_latest_tag_aseprite() -> str:
    return 'beta' # Return early for beta.
    releases = download_json(f"https://api.github.com/repos/{MAIN_REPO}/releases?per_page=100")
    for release in releases:
        tag_name = release.get("tag_name", "")
        if (
            tag_name
            and "beta" not in tag_name.lower()
            and not release.get("draft", False)
            and not release.get("prerelease", False)
        ):
            return tag_name
    raise RuntimeError("No stable Aseprite release was found.")

def clone_aseprite(tag: str) -> None:
    clone_url = f"https://github.com/{MAIN_REPO}.git"
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    if MAIN_REPO_DIR.exists():
        print(f"Removing existing directory: {MAIN_REPO_DIR}")
        shutil.rmtree(MAIN_REPO_DIR)
    subprocess.run(["git","clone","--branch",tag,"--depth","1",clone_url,str(MAIN_REPO_DIR),],check=True,)
    subprocess.run(["git","submodule","update","--init","--recursive","--depth","1",],cwd=MAIN_REPO_DIR,check=True,)

def download_dependency_skia(tag: str):
    print(f"Using Skia release: {tag}")
    download_url = (f"https://github.com/aseprite/skia/releases/download/{tag}/Skia-Windows-Release-x64.zip")
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    if SKIA_DIR.exists():
        print(f"Removing existing directory: {SKIA_DIR}")
        shutil.rmtree(SKIA_DIR)
    print(f"Downloading Skia from: {download_url}")
    download_file(download_url, SKIA_ZIP_PATH)
    print(f"Extracting Skia to: {SKIA_DIR}")
    SKIA_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(SKIA_ZIP_PATH, "r") as archive:
        archive.extractall(SKIA_DIR)
    SKIA_ZIP_PATH.unlink()

def main() -> None:
    main_tag = get_latest_tag_aseprite()
    print(f"Latest stable Aseprite release: {main_tag}")

    clone_aseprite(main_tag)
    VERSION_FILE.write_text(main_tag, encoding="utf-8") # Save tag.

    download_dependency_skia('m151-a90155cff0')
    print("Aseprite and Skia downloaded successfully.")

if __name__ == "__main__":
    main()
