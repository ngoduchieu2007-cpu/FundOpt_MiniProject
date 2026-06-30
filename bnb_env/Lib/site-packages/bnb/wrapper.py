from pathlib import Path
from functools import lru_cache

from bnb.config import Config


class Wrapper:
    def __init__(self, config=None):
        self.cfg = config or Config()

    @lru_cache
    def _get_html(self, subpath):
        path = Path(self.cfg.home).joinpath(subpath)
        with open(path) as f:
            return f.read()

    def get_header(self):
        return self._get_html(self.cfg.header_file)

    def get_sidebar(self):
        return self._get_html(self.cfg.sidebar_file)

    def get_footer(self):
        return self._get_html(self.cfg.footer_file)

    def inject_content(self, content, overview):
        header = self.get_header()
        sidebar = self.get_sidebar()
        footer = self.get_footer()
        result = f"{header}{content}{sidebar}{overview}{footer}"

        return result

    def run(self, conv_content, overview):
        return self.inject_content(conv_content.content, overview)
