import yaml
import logging

import attr

from bnb.config import Config
from bnb.exceptions import BoundsNotFound


logger = logging.getLogger(__name__)


@attr.s
class ExtractedContent:
    path = attr.ib()
    markdown = attr.ib()
    metadata = attr.ib()


class Extractor:
    """Reads the file at path provided and returns relevant lines."""

    def __init__(self, config=None):
        self.cfg = config or Config()

    def run(self, path):
        content = self._read_file(path)

        return ExtractedContent(
            path=path,
            markdown=self.extract_markdown(content),
            metadata=self.extract_metadata(content),
        )

    def _read_file(self, fpath):
        logger.info(f"Reading file at: {fpath}")
        with open(fpath, "r") as f:
            return f.readlines()

    def _get_content_boundaries(self, content, open_, close_):
        try:
            from_ = content.index(open_)
            to_ = content.index(close_)
        except ValueError as verr:
            msg = f"Boundary is missing in text-content:\n{verr}"
            raise BoundsNotFound(msg)

        return from_, to_

    def extract_markdown(self, content):
        from_, to_ = self._get_content_boundaries(
            content, self.cfg.markdown_open, self.cfg.markdown_close
        )

        markdown = content[(from_ + 1) : to_]

        return [l[2:] for l in markdown]

    def extract_metadata(self, content):
        from_, to_ = self._get_content_boundaries(
            content, self.cfg.markdown_open, self.cfg.markdown_close
        )

        meta_start = content[0:from_]
        meta_end = content[(to_ + 1) :]

        return [l.strip() for l in (meta_start + meta_end)]
