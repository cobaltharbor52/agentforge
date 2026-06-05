"""Unit tests for text utilities."""

from contentforge.utils.text import (
    extract_frontmatter,
    reading_time,
    slugify,
    truncate,
    word_count,
)
from contentforge.utils.export import export_markdown, export_html


class TestWordCount:
    def test_english_text(self):
        assert word_count("Hello world this is a test") == 6

    def test_empty_string(self):
        assert word_count("") == 0

    def test_cjk_text(self):
        assert word_count("你好世界") == 4

    def test_mixed_text(self):
        count = word_count("Hello 世界 world")
        # "Hello" = 1 english, "世界" = 2 CJK, "world" = 1 english = 4
        assert count == 4

    def test_whitespace_only(self):
        assert word_count("   ") == 0


class TestTruncate:
    def test_short_text(self):
        assert truncate("Hello", 100) == "Hello"

    def test_long_text(self):
        result = truncate("A" * 200, 50)
        assert len(result) == 50
        assert result.endswith("...")

    def test_custom_suffix(self):
        result = truncate("A" * 200, 50, suffix="…")
        assert result.endswith("…")


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hello, World! @2024") == "hello-world-2024"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_leading_trailing(self):
        assert slugify("  hello  ") == "hello"


class TestReadingTime:
    def test_short_text(self):
        assert "1 min" in reading_time("Hello world")

    def test_medium_text(self):
        text = " ".join(["word"] * 400)
        assert "2 min" in reading_time(text)

    def test_long_text(self):
        text = " ".join(["word"] * 2000)
        assert "10 min" in reading_time(text)


class TestExtractFrontmatter:
    def test_with_frontmatter(self):
        text = "---\ntitle: Test\nauthor: Me\n---\n\nContent here"
        fm, content = extract_frontmatter(text)
        assert fm["title"] == "Test"
        assert fm["author"] == "Me"
        assert "Content here" in content

    def test_without_frontmatter(self):
        text = "No frontmatter here"
        fm, content = extract_frontmatter(text)
        assert fm == {}
        assert content == "No frontmatter here"


class TestExportMarkdown:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "test.md"
        export_markdown("# Hello", {"title": "Test"}, path)
        assert path.exists()
        content = path.read_text()
        assert "---" in content
        assert "title: Test" in content
        assert "# Hello" in content


class TestExportHTML:
    def test_creates_valid_html(self, tmp_path):
        path = tmp_path / "test.html"
        export_html("# Hello World", {"title": "Test", "description": "A test"}, path)
        assert path.exists()
        content = path.read_text()
        assert "<!DOCTYPE html>" in content
        assert "<title>Test</title>" in content
        assert "ContentForge" in content
