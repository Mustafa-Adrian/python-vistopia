import requests
from urllib.parse import urljoin
from urllib.request import urlretrieve, urlcleanup
from logging import getLogger
from functools import lru_cache
from typing import List, Optional
from pathvalidate import sanitize_filename
import click

from .models import (
    Article,
    Catalog,
    ContentShow,
    RetagArticle,
    RetagSeries,
    SearchResult,
    SubscriptionsList,
    SubscriptionItem,
    validate_model,
)

logger = getLogger(__name__)


class Visitor:
    def __init__(self, token: Optional[str]):
        self.token = token

    def get_api_response(self, uri: str, params: Optional[dict] = None):

        url = urljoin("https://api.vistopia.com.cn/api/v1/", uri)

        if params is None:
            params = {}

        params.update({"api_token": self.token})

        logger.debug(f"Visiting {url}")

        response = requests.get(url, params=params).json()
        assert response["status"] == "success"
        assert "data" in response.keys()

        return response["data"]

    @lru_cache()
    def get_catalog(self, id: int):
        response = self.get_api_response(f"content/catalog/{id}")
        return validate_model(Catalog, response)

    @lru_cache()
    def get_user_subscriptions_list(self):
        data: List[SubscriptionItem] = []
        while True:
            response = self.get_api_response("user/subscriptions-list")
            subscriptions = validate_model(SubscriptionsList, response)
            data.extend(subscriptions.data)
            break
        return data

    @lru_cache()
    def search(self, keyword: str) -> list:
        response = self.get_api_response("search/web", {'keyword': keyword})
        result = validate_model(SearchResult, response)
        return result.data

    @lru_cache()
    def get_content_show(self, id: int):
        response = self.get_api_response(f"content/content-show/{id}")
        return validate_model(ContentShow, response)

    def save_show(self, id: int,
                  no_tag: bool = False, no_cover: bool = False,
                  episodes: Optional[set] = None,
                  skip_first: int = 0,
                  skip_existing: bool = False,
                  playlist_only: bool = False,
                  show_index: int = 1,
                  show_total: int = 1):

        from pathlib import Path

        show_prefix = "Show {}/{}".format(show_index, show_total)
        catalog = self.get_catalog(id)

        show_dir = Path(catalog.title)
        show_dir.mkdir(exist_ok=True)

        catalog_items = self._iter_catalog_items(catalog, episodes)
        self.write_playlist_files(show_dir, catalog_items)
        episode_total = len(catalog_items)
        click.echo(
            "{} catalog ready: id={}, title={}, episodes={}".format(
                show_prefix,
                id,
                catalog.title,
                episode_total,
            )
        )

        if playlist_only:
            click.echo(
                "{} playlist-only completed: id={}, title={}".format(
                    show_prefix,
                    id,
                    catalog.title,
                )
            )
            return

        series = self.get_content_show(id)

        for episode_index, (article, fname) in enumerate(catalog_items, start=1):
            episode_prefix = "{} episode {}/{}".format(
                show_prefix,
                episode_index,
                episode_total,
            )
            if skip_first > 0:
                click.echo(
                    "{} skipped by --skip-first: {}".format(
                        episode_prefix,
                        article.title,
                    )
                )
                skip_first -= 1
                continue

            fname_exists = fname.exists()
            fname_size = fname.stat().st_size if fname_exists else 0

            if skip_existing and fname_exists and fname_size > 0:
                click.echo(
                    "{} skipped existing: api_sort_number={}, file={}".format(
                        episode_prefix,
                        article.sort_number,
                        fname,
                    )
                )
                continue

            if not fname_exists or fname_size == 0:
                click.echo(
                    "{} downloading: api_sort_number={}, title={}".format(
                        episode_prefix,
                        article.sort_number,
                        article.title,
                    )
                )
                self._download_to_file(article.media_key_full_url, fname)
                click.echo(
                    "{} saved: file={}".format(episode_prefix, fname)
                )
            else:
                click.echo(
                    "{} using existing: api_sort_number={}, file={}".format(
                        episode_prefix,
                        article.sort_number,
                        fname,
                    )
                )

            if not no_tag:
                self.retag(str(fname), article, catalog, series)

            if not no_cover:
                self.retag_cover(str(fname), article, catalog, series)

        click.echo(
            "{} completed: id={}, title={}".format(
                show_prefix,
                id,
                catalog.title,
            )
        )

    @staticmethod
    def _iter_catalog_items(catalog: Catalog, episodes: Optional[set] = None):
        from pathlib import Path

        show_dir = Path(catalog.title)
        catalog_items = []
        for part in catalog.catalog:
            for article in part.part:
                if episodes and int(article.sort_number) not in episodes:
                    continue

                fname = show_dir / "{}.mp3".format(
                    sanitize_filename(article.title)
                )
                catalog_items.append((article, fname))
        return catalog_items

    @staticmethod
    def write_playlist_files(show_dir, catalog_items):
        playlist_fname = show_dir / "playlist.m3u8"
        catalog_fname = show_dir / "catalog.tsv"

        with open(playlist_fname, "w", encoding="utf-8") as fp:
            fp.write("#EXTM3U\n")
            for article, fname in catalog_items:
                fp.write("#EXTINF:-1,{}\n".format(article.title))
                fp.write("{}\n".format(fname.name))

        with open(catalog_fname, "w", encoding="utf-8") as fp:
            fp.write("index\ttitle\tapi_sort_number\tfilename\n")
            for index, (article, fname) in enumerate(catalog_items, start=1):
                fp.write("{}\t{}\t{}\t{}\n".format(
                    index,
                    article.title,
                    article.sort_number,
                    fname.name,
                ))

        click.echo("Wrote playlist: {}".format(playlist_fname))
        click.echo("Wrote catalog: {}".format(catalog_fname))

    @staticmethod
    def _download_to_file(url: str, fname):
        """Download to a temp file first so interrupted runs are resumable."""
        tmp_fname = fname.with_suffix(fname.suffix + ".part")
        urlretrieve(url, str(tmp_fname))
        tmp_fname.replace(fname)

    def save_transcript(self, id: int, episodes: Optional[set] = None):

        from pathlib import Path

        catalog = self.get_catalog(id)

        show_dir = Path(catalog.title)
        show_dir.mkdir(exist_ok=True)

        for part in catalog.catalog:
            for article in part.part:

                if episodes and \
                        int(article.sort_number) not in episodes:
                    continue

                fname = show_dir / "{}.html".format(
                    sanitize_filename(article.title)
                )
                if not fname.exists():
                    urlretrieve(article.content_url, fname)

                    with open(fname) as f:
                        content = f.read()

                    content = content.replace(
                        "/assets/article/course.css",
                        "https://api.vistopia.com.cn/assets/article/course.css"
                    )

                    with open(fname, "w") as f:
                        f.write(content)

    def save_transcript_with_single_file(self, id: int,
                                         episodes: Optional[set] = None,
                                         single_file_exec_path: str = "",
                                         cookie_file_path: str = ""):
        import subprocess
        from pathlib import Path
        logger.debug(f"save_transcript_with_single_file id {id}")

        catalog = self.get_catalog(id)
        show_dir = Path(catalog.title)
        show_dir.mkdir(exist_ok=True)

        for part in catalog.catalog:
            for article in part.part:
                if episodes and int(article.sort_number) not in episodes:
                    continue

                fname = show_dir / "{}.html".format(
                    sanitize_filename(article.title)
                )
                if not fname.exists():
                    command = [
                        single_file_exec_path,
                        "https://www.vistopia.com.cn/article/"
                        + article.article_id,
                        str(fname),
                        "--browser-cookies-file=" + cookie_file_path
                    ]
                    logger.debug(f"singlefile command {command}")
                    try:
                        subprocess.run(command, check=True)
                        print(
                            f"Successfully fetched and saved to {fname}")
                    except subprocess.CalledProcessError as e:
                        print(f"Failed to fetch page using single-file: {e}")

    @staticmethod
    def retag(
        fname: str,
        article_info: RetagArticle,
        catalog_info: Catalog,
        series_info: RetagSeries
    ):

        from mutagen.easyid3 import EasyID3
        from mutagen.id3 import ID3NoHeaderError

        try:
            track = EasyID3(fname)
        except ID3NoHeaderError:
            # No ID3 tag found, creating a new ID3 tag
            # See: https://github.com/quodlibet/mutagen/issues/327
            track = EasyID3()

        track['title'] = article_info.title
        track['album'] = series_info.title
        track['artist'] = series_info.author
        track['tracknumber'] = str(article_info.sort_number)
        track['website'] = article_info.content_url

        try:
            track.save(fname)
        except Exception as e:
            print(f"Error saving ID3 tags: {e}")

    @staticmethod
    def retag_cover(fname, article_info, catalog_info: Catalog, series_info):

        from mutagen.id3 import ID3, APIC

        @lru_cache()
        def _get_cover(url: str) -> bytes:
            cover_fname, _ = urlretrieve(url)
            with open(cover_fname, "rb") as fp:
                cover = fp.read()
            urlcleanup()
            return cover

        cover = _get_cover(catalog_info.background_img)

        track = ID3(fname)
        track["APIC"] = APIC(encoding=3, mime="image/jpeg",
                             type=3, desc="Cover", data=cover)
        track.save()
