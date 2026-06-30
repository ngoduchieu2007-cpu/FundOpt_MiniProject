from pathlib import Path
from datetime import datetime
from collections import defaultdict

import click
import markdown
import questionary

from bnb.config import Config
from bnb.writer import Writer
from bnb.scanner import Scanner
from bnb.wrapper import Wrapper
from bnb.extractor import Extractor
from bnb.converter import Converter
from bnb.exceptions import ConfigurationError


@click.command()
@click.option("--home", "-h", default=None, type=str)
@click.option("--automated", "-a", default=True, type=bool)
def cli(home=None, automated=True):
    if not home:
        msg = "Hi there! What folder should we set as the home of your blog?"
        home = questionary.text(msg, default=Config().home_folder).ask()

    cfg = Config(home=home, automated=automated)
    blogger = Blogger(cfg)
    blogger.run()

    print("All done!")


class Blogger:
    def __init__(self, config=None):
        self.cfg = config or Config()

    def _assert_settings_file(self):
        settings = self.cfg.home.joinpath(self.cfg.bnote_settings_file)
        if not settings.exists():
            msg = f"{self.cfg.bnote_settings_file} could not be found at {self.cfg.home}."
            raise ConfigurationError(msg)

    def _assert_assets_folder(self):
        assets = self.cfg.home.joinpath(self.cfg.assets_folder)
        if not assets.exists():
            msg = f"No assets folder found at {self.cfg.home}."
            raise ConfigurationError(msg)

    def _assert_notes_folder(self):
        notes = self.cfg.home.joinpath(self.cfg.notes_folder)
        if not notes.exists():
            msg = f"No notes folder found at {self.cfg.home}."
            raise ConfigurationError(msg)

    def assert_setup(self):
        try:
            self._assert_notes_folder()
            self._assert_assets_folder()
            self._assert_settings_file()
        except ConfigurationError as e:
            msg = (
                f"Something went wrong trying to set the blog-home:\n"
                f"{e}\n"
                f"Exiting."
            )
            print(msg)
            exit()

    def scan_files(self, scanner=None):
        scanner = scanner or Scanner(self.cfg)

        return scanner.run(self.cfg.home)

    def process_files(self, files, extractor=None, converter=None):
        processed = []

        extractor = extractor or Extractor(self.cfg)
        converter = converter or Converter(self.cfg)

        for file in files:
            extracted = extractor.run(file)
            processed.append(converter.run(extracted))

        return processed

    def confirm_for_conversion(self, files):
        if self.cfg.automated:
            return files

        msg = f"We found {len(files)} files, deselect to omit."
        choices = [questionary.Choice(f, checked=True) for f in files]

        return questionary.checkbox(msg, choices=choices).ask()

    def _get_chronological_file_map(self, files):
        result = defaultdict(list)
        files.sort(key=lambda f: f.metadata["createdAt"][:7], reverse=True)

        for file in files:
            created = datetime.strptime(file.metadata["createdAt"][:7], "%Y-%m")
            result[created.strftime("%B %Y")].append(file.md_link)

        return result

    def get_files_overview(self, files):
        sidebar_md = []
        mapping = self._get_chronological_file_map(files)

        for key, values in mapping.items():
            links = "\n".join([f"* {v}" for v in values])
            sidebar_md.append(f"## {key}\n{links}")

        return markdown.Markdown(output_format="html").convert("\n".join(sidebar_md))

    def wrap_in_html(self, content, overview, wrapper=None):
        wrapper = wrapper or Wrapper(self.cfg)
        for file in content:
            wrapped = wrapper.run(file, overview)
            file.content = wrapped

        return content

    def write_output(self, content, writer=None):
        writer = writer or Writer(self.cfg)
        for file in content:
            writer.run(file)

    def run(self):
        self.assert_setup()

        scanned = self.scan_files()
        processed = self.process_files(scanned)
        confirmed = self.confirm_for_conversion(processed)
        overview = self.get_files_overview(confirmed)
        wrapped_content = self.wrap_in_html(confirmed, overview)

        self.write_output(wrapped_content)
