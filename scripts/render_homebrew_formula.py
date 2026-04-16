#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


TEMPLATE = """class Clawbackup < Formula
  include Language::Python::Virtualenv

  desc "OpenClaw backup utility CLI"
  homepage "{homepage}"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.11"

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-15.0.0.tar.gz"
    sha256 "edd07a4824c6b40189fb7ac9bc4c52536e9780fbbfbddf6f1e2502c31b068c36"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/source/m/markdown-it-py/markdown_it_py-4.0.0.tar.gz"
    sha256 "cb0a2b4aa34f932c007117b194e945bd74e0ec24133ceb5bac59009cda1cb9f3"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/source/m/mdurl/mdurl-0.1.2.tar.gz"
    sha256 "bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/source/p/pygments/pygments-2.20.0.tar.gz"
    sha256 "6757cd03768053ff99f3039c1a36d6c0aa0b263438fcab17520b30a303a82b5f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{{bin}}/clawbackup --help")
    assert_match "ClawBackup", output
  end
end
"""


def sha256_for(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Homebrew formula for ClawBackup.")
    parser.add_argument("archive", help="Path to the source tar.gz archive.")
    parser.add_argument(
        "--homepage",
        default="https://github.com/Huifu1018/ClawBackup",
    )
    parser.add_argument(
        "--url",
        help="Release tarball URL. Defaults to file://<archive> for local testing.",
    )
    parser.add_argument(
        "--github-repo",
        help="GitHub repo in owner/name form. If set, generate a GitHub Releases tarball URL.",
    )
    parser.add_argument(
        "--tag",
        default="v0.1.1",
        help="Release tag to use with --github-repo. Default: v0.1.1",
    )
    parser.add_argument(
        "--output",
        default="Formula/clawbackup.rb",
        help="Where to write the generated formula.",
    )
    args = parser.parse_args()

    archive = Path(args.archive).resolve()
    if args.url:
        url = args.url
    elif args.github_repo:
        url = (
            f"https://github.com/{args.github_repo}/releases/download/"
            f"{args.tag}/{archive.name}"
        )
    else:
        url = archive.as_uri()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    formula = TEMPLATE.format(
        homepage=args.homepage,
        url=url,
        sha256=sha256_for(archive),
    )
    output.write_text(formula, encoding="utf-8")
    print(output.resolve())


if __name__ == "__main__":
    main()
