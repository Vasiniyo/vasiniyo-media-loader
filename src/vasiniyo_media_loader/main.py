from collections import defaultdict
import json
import logging
import os
from pathlib import Path
from queue import Queue
import shutil
import sys
import threading

from yt_dlp import YoutubeDL
from yt_dlp.utils import YoutubeDLError

from vasiniyo_media_loader.logger.logger import LogFormatter

logger = logging.getLogger(__name__)


class Cache:
    _file: Path
    _data: defaultdict[str, set[str]] | None

    def __init__(self, file_path: str) -> None:
        self._file = Path(file_path)
        self._data = None

    def add(self, url: str, title: str) -> None:
        if self._data is None:
            self.upload_data()
        if url in self._data and title in self._data[url]:
            return
        self._data[url].add(title)
        with self._file.open("a", encoding="utf-8") as file:
            file.write(self._encode(url, title) + "\n")

    def remove(self, url: str, title: str) -> None:
        if self._data is None:
            self.upload_data()
        self._data[url].discard(title)

    def get(self, url: str) -> set[str]:
        if self._data is None:
            self.upload_data()
        if url in self._data:
            return set(self._data[url])
        return set()

    def upload_data(self) -> None:
        self._data = defaultdict(set)
        if not self._file.exists():
            self._file.touch()
            return
        for line in self._file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            url, title = self._decode(line)
            if not (url and title):
                logger.warning(
                    "invalid_cache", extra={"line": line, "url": url, "title": title}
                )
                continue
            if self._file.exists():
                self._data[url].add(title)
            else:
                logger.warning("file_removed", extra={"path": title})
        with self._file.open("w", encoding="utf-8") as file:
            file.writelines(
                [
                    self._encode(url, title) + "\n"
                    for url in self._data
                    for title in self._data[url]
                ]
            )

    @staticmethod
    def _encode(url: str, title: str) -> str:
        return json.dumps({"url": url, "title": title}, ensure_ascii=False)

    @staticmethod
    def _decode(line: str) -> tuple[str | None, str | None]:
        try:
            obj = json.loads(line)
            url = obj.get("url")
            title = obj.get("title")
            return url, title
        except json.decoder.JSONDecodeError:
            return None, None


class Mp3Service:
    _ydl = None

    def __init__(self, out_dir: str, cookiefile: str, cache: Cache) -> None:
        self._out_dir = Path(out_dir)
        self.cookiefile = cookiefile
        self._cache = cache
        self._mp3_opts = {
            "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
            "verbose": logger.level == logging.DEBUG,
            "quiet": logger.level != logging.DEBUG,
            "logger": logger,
            "format": "bestaudio/best",
            "remote_components": ["ejs:github"],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "0",
                }
            ],
        }

    def get_ydl(self) -> YoutubeDL:
        if self._ydl:
            return self._ydl
        logger.info("getting_cookie")
        self._ydl = YoutubeDL(self._mp3_opts | {"cookiefile": self.cookiefile})
        return self._ydl

    def download(self, url: str) -> None:
        for cached_path in self._cache.get(url):
            if not os.path.exists(cached_path):
                self._cache.remove(url, cached_path)
                logger.warning(f"cache_miss", extra={"url": url, "path": cached_path})
                continue
            src = Path(cached_path)
            dst = self._out_dir / src.name
            if dst.exists():
                logger.info("already_exists", extra={"url": url, "path": cached_path})
                self._cache.add(url, dst.as_posix())
                return
            shutil.copy(src, self._out_dir)
            logger.info("copied", extra={"url": url, "path": dst})
            return
        with self.get_ydl() as ydl:
            info = ydl.extract_info(url, download=True)
            filename = os.path.splitext(ydl.prepare_filename(info))[0]
            ext = self._mp3_opts["postprocessors"][0]["preferredcodec"]
            file_path = f"{filename}.{ext}"
            self._cache.add(url, file_path)
            logger.info("downloaded", extra={"url": url, "path": file_path})


def download_audio(mp3_service: Mp3Service, url: str) -> bool:
    try:
        mp3_service.download(url)
        return True
    except YoutubeDLError as e:
        logger.warning("download_failed", extra={"url": url, "cause": str(e)})
        return False
    except Exception:
        logger.exception("download_failed", extra={"url": url})
        return False


def worker(queue: Queue, mp3_service: Mp3Service, stop_event: threading.Event) -> None:
    while True:
        if stop_event.is_set():
            break
        try:
            url = queue.get()
            if url is None:
                break
            status = download_audio(mp3_service, url)
            logger.info(
                "download_status",
                extra={"url": url, "status": "success" if status else "failure"},
            )
            print(f"[{'+' if status else '-'}] {url}")
        finally:
            queue.task_done()


def main() -> int:
    output = os.environ.get("OUTPUT_PATH", "ytloads/common")
    debug_mode = os.environ.get("DEBUG", False)
    quiet_mode = os.environ.get("QUIET_MODE", False)
    cookiefile = os.environ.get("COOKIES_PATH")
    log_file = os.environ.get("LOG_FILE")
    logging_level = logging.DEBUG if debug_mode else logging.INFO
    logger.setLevel(logging_level)
    log_formatter = LogFormatter()
    if not quiet_mode:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(log_formatter)
        logger.addHandler(stderr_handler)
    if log_file:
        file_logger = logging.FileHandler(log_file)
        file_logger.setFormatter(log_formatter)
        logger.addHandler(file_logger)
    queue = Queue()
    mp3_service = Mp3Service(output, cookiefile, Cache("ytloads/.cache-ytd.jsonl"))
    exit_status = 0
    try:
        stop_event = threading.Event()
        worker_thread = threading.Thread(
            target=worker, args=(queue, mp3_service, stop_event)
        )
        worker_thread.start()
        try:
            for line in sys.stdin:
                queue.put(line.rstrip("\n").strip())
            queue.put(None)
            queue.join()
        except KeyboardInterrupt:
            print(
                "Finishing current task... Press Ctrl+C again to force exit",
                file=sys.stderr,
            )
            exit_status = 1
        finally:
            logger.debug(
                "waiting_thread_join",
                extra={
                    "worker_name": worker_thread.name,
                    "worker_status": "alive" if worker_thread.is_alive() else "dead",
                },
            )
            stop_event.set()
            worker_thread.join()
    except KeyboardInterrupt:
        exit_status = 1
    except Exception:
        logger.exception("unexpected_error")
        exit_status = 1
    finally:
        return exit_status


if __name__ == "__main__":
    raise SystemExit(main())
