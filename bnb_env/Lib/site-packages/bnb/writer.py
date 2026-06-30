import os
import logging
from pathlib import Path

from bnb.config import Config


logger = logging.getLogger(__name__)


class Writer:
    """Builds new path and writes content to file."""

    def __init__(self, config=None):
        self.cfg = config or Config()

    def _create_if_not_present(self, path):
        if not os.path.exists(path.parent):
            msg = f"Creating directories {path.parent}."
            logger.info(msg)
            os.makedirs(path.parent)

    def _create_file(self, path, content):
        self._create_if_not_present(path)
        with open(path, "w") as f:
            f.write(content)

    def _construct_new_path(self, conv_content):
        injection = self.cfg.output_folder
        folder = conv_content.folder
        fname = conv_content.filename

        subpath = (injection, folder, fname)
        if conv_content.is_index:
            subpath = (fname,)

        parts = conv_content.path.absolute().parts
        notes = parts.index(self.cfg.notes_folder)

        return Path(*parts[:notes]).joinpath(*subpath)

    def run(self, converted_content):
        path = self._construct_new_path(converted_content)
        self._create_file(path, converted_content.content)
