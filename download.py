import json
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path


ASEPRITE_REPOSITORY = "aseprite/aseprite"
SKIA_REPOSITORY = "aseprite/skia"
SKIA_RELEASE_FILE_NAME = "Skia-Windows-Release-x64.zip"

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
ASEPRITE_DIR = SRC_DIR / "aseprite"
SKIA_DIR = SRC_DIR / "skia"
SKIA_ZIP_PATH = SRC_DIR / SKIA_RELEASE_FILE_NAME
VERSION_FILE = ROOT_DIR / "version.txt"


def download_json(url: str):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "aseprite-auto-build",
        },
    )

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
    releases_url = (
        f"https://api.github.com/repos/"
        f"{ASEPRITE_REPOSITORY}/releases?per_page=100"
    )

    releases = download_json(releases_url)

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


def save_aseprite_tag(tag: str) -> None:
    VERSION_FILE.write_text(tag, encoding="utf-8")


def clone_aseprite(tag: str) -> None:
    clone_url = f"https://github.com/{ASEPRITE_REPOSITORY}.git"

    SRC_DIR.mkdir(parents=True, exist_ok=True)

    if ASEPRITE_DIR.exists():
        print(f"Removing existing directory: {ASEPRITE_DIR}")
        shutil.rmtree(ASEPRITE_DIR)

    subprocess.run(
        [
            "git",
            "clone",
            "--branch",
            tag,
            "--depth",
            "1",
            clone_url,
            str(ASEPRITE_DIR),
        ],
        check=True,
    )

    subprocess.run(
        [
            "git",
            "submodule",
            "update",
            "--init",
            "--recursive",
            "--depth",
            "1",
        ],
        cwd=ASEPRITE_DIR,
        check=True,
    )


def get_latest_tag_skia() -> str:
    return "m124-08a5439a6b"


def download_skia_for_windows(tag: str) -> None:
    download_url = (
        f"https://github.com/{SKIA_REPOSITORY}/releases/download/"
        f"{tag}/{SKIA_RELEASE_FILE_NAME}"
    )

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
    aseprite_tag = get_latest_tag_aseprite()
    print(f"Latest stable Aseprite release: {aseprite_tag}")

    clone_aseprite(aseprite_tag)
    save_aseprite_tag(aseprite_tag)

    skia_tag = get_latest_tag_skia()
    print(f"Using Skia release: {skia_tag}")

    download_skia_for_windows(skia_tag)

    print("Aseprite and Skia downloaded successfully.")


if __name__ == "__main__":
    main()
