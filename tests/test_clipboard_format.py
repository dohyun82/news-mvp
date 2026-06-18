import unittest

from shared.integrations.clipboard import format_clipboard_text, format_clipboard_html
from core.categories import UNCATEGORIZED


class TestClipboardFormat(unittest.TestCase):
    def test_empty(self):
        self.assertIn("선택된 기사가 없습니다", format_clipboard_text([]))
        self.assertIn("선택된 기사가 없습니다", format_clipboard_html([]))

    def test_groups_in_defined_order_with_icon(self):
        arts = [
            {"title": "B기사", "url": "http://b", "category": "플랫폼·테크", "summary": "S2"},
            {"title": "A기사", "url": "http://a", "category": "그룹사", "summary": "S1"},
        ]
        text = format_clipboard_text(arts)
        # 그룹사가 플랫폼·테크보다 먼저 (NEWS_CATEGORIES 정의 순서)
        self.assertLess(text.index("그룹사"), text.index("플랫폼·테크"))
        self.assertIn("🏢", text)
        self.assertIn("http://a", text)
        self.assertIn("S1", text)

    def test_uncategorized_goes_last(self):
        arts = [
            {"title": "미분류기사", "url": "http://u", "category": UNCATEGORIZED},
            {"title": "그룹사기사", "url": "http://g", "category": "그룹사"},
        ]
        text = format_clipboard_text(arts)
        self.assertLess(text.index("그룹사"), text.index(UNCATEGORIZED))

    def test_html_has_anchor_links(self):
        arts = [{"title": "제목", "url": "http://x", "category": "그룹사"}]
        html = format_clipboard_html(arts)
        self.assertIn('<a href="http://x">제목</a>', html)


if __name__ == "__main__":
    unittest.main()
