import logging
import pathlib

import yaml
import attr
import markdown

from bnb.config import Config
from bnb.exceptions import FolderCouldNotBeMapped


logger = logging.getLogger(__name__)


@attr.s
class ConvertedContent:
    path = attr.ib(converter=pathlib.Path)
    content = attr.ib(converter=str)
    metadata = attr.ib(converter=dict)

    cfg = attr.ib(default=attr.Factory(Config))

    @property
    def title(self):
        return self.metadata["title"]

    @property
    def filename(self):
        lowered = self.title.lower().replace(" ", "_")
        return f"{lowered}{self.cfg.output_extension}"

    @property
    def tags(self):
        return self.metadata["tags"]

    @property
    def folder(self):
        metafold = self.metadata.get("folder")

        if folder := self.cfg.folders.get(metafold):
            return folder

        msg = f"Key {metafold} could not be found" f" in mapping {self.cfg.folders}"
        raise FolderCouldNotBeMapped(msg)

    @property
    def is_index(self):
        return (
            self.folder == self.cfg.index_folder
            and self.filename == self.cfg.index_file
        )

    @property
    def md_link(self):
        md = markdown.Markdown(output_format="html")

        title = (
            f"[{self.folder} - {self.title}]"
        )
        parts = [self.cfg.base_url, self.filename]
        if not self.is_index:
            parts[1:1] = [self.cfg.output_folder, self.folder]

        link = f"({'/'.join(parts)})"
        tags = f"**{' - '.join([t for t in self.tags])}**"

        return md.convert(f"{title}{link}{tags if self.tags else ''}")

    def __str__(self):
        return f"{self.folder} - {self.title} (tags: {self.tags})"


class Converter:
    """Turns list of string into dict and html-markdown."""

    _glue = "\n"

    def __init__(self, config=None):
        self.cfg = config or Config()
        self.md = markdown.Markdown(output_format="html", extensions=["fenced_code"])

    def _glue_content(self, lines):
        return self._glue.join(lines)

    def _convert_markdown(self, content):
        if not content:
            logger.warning("Content empty, cannot be converted to markdown!")

        # return self.md.convert(self._glue_content(content))
        return self.md.convert("".join(content))

    def _convert_metadata(self, content):
        if not content:
            logger.warning("Content empty, cannot be converted to metadata!")

        return yaml.safe_load(self._glue_content(content))

    def run(self, extracted_content):
        logger.info(f"Converting content at {extracted_content.path}")

        return ConvertedContent(
            cfg=self.cfg,
            path=extracted_content.path,
            content=self._convert_markdown(extracted_content.markdown),
            metadata=self._convert_metadata(extracted_content.metadata),
        )
