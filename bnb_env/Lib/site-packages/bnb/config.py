import os
import json
import logging
from pathlib import Path
from functools import cached_property

import attr
from smart_getenv import getenv

from bnb.exceptions import FolderCouldNotBeMapped


logger = logging.getLogger(__name__)


@attr.s
class ConfigOption:
    name = attr.ib()
    default = attr.ib()
    _type = attr.ib(default=str)

    @property
    def key(self):
        return self.name.lower()

    @property
    def value(self):
        return getenv(name=self.name, type=self._type, default=self.default)


# This is purely used to store the default config options
_defaults = (
    ConfigOption("MARKDOWN_OPEN", "content: '''\n"),
    ConfigOption("MARKDOWN_CLOSE", "'''\n"),
    ConfigOption("MARKDOWN_EXTENSION", ".md"),
    ConfigOption("METADATA_EXTENSION", ".yml"),
    ConfigOption("CSON_EXTENSION", ".cson"),
    ConfigOption("OUTPUT_EXTENSION", ".html"),
    ConfigOption("INDEX_FILE", "index.html"),
    ConfigOption("METADATA_FOLDER", "meta"),
    ConfigOption("OUTPUT_FOLDER", "build"),
    ConfigOption("NOTES_FOLDER", "notes"),
    ConfigOption("ASSETS_FOLDER", "assets"),
    ConfigOption("INDEX_FOLDER", "Default"),
    ConfigOption("HOME_FOLDER", "/home/bram/dev/bramver.github.io"),
    ConfigOption("HEADER_FILE", "assets/header.html"),
    ConfigOption("SIDEBAR_FILE", "assets/sidebar.html"),
    ConfigOption("FOOTER_FILE", "assets/footer.html"),
    ConfigOption("BASE_URL", "https://bramver.github.io"),
    ConfigOption("BNOTE_SETTINGS_FILE", "boostnote.json"),
)


class Config:
    def __init__(self, home=None, bnote_settings=None, **kwargs):
        for option in _defaults:
            setattr(self, option.key, option.value)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self.home = Path(home or self.home_folder)
        self.bnote_settings = bnote_settings

    def read_boostnote_settings(self):
        path = Path(self.home).joinpath(self.bnote_settings_file)

        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError:
            msg = "Error: Could not locate the Boostnote Settings File at '{}'"
            logger.error(msg.format(path))
            raise FolderCouldNotBeMapped(msg)

        self.bnote_settings = data
        return data

    @cached_property
    def folders(self):
        if not self.bnote_settings:
            self.read_boostnote_settings()

        return {f["key"]: f["name"] for f in self.bnote_settings["folders"]}
