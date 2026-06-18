import unittest

from shared.integrations.clipboard import format_clipboard_text, format_clipboard_html
from core.categories import UNCATEGORIZED, CLIPBOARD_FOOTER


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
        self.assertIn("💚", text)
        self.assertIn("🛠️", text)
        self.assertIn("http://a", text)
        self.assertIn("○ S1", text)  # 요약은 하위 들여쓰기(○)

    def test_uncategorized_goes_last(self):
        arts = [
            {"title": "미분류기사", "url": "http://u", "category": UNCATEGORIZED},
            {"title": "그룹사기사", "url": "http://g", "category": "그룹사"},
        ]
        text = format_clipboard_text(arts)
        self.assertLess(text.index("그룹사"), text.index(UNCATEGORIZED))

    def test_readworthy_category_supported(self):
        arts = [{"title": "읽을거리기사", "url": "http://r", "category": "읽을거리"}]
        text = format_clipboard_text(arts)
        self.assertIn("🌐", text)
        self.assertIn("읽을거리", text)

    def test_html_bold_anchor_and_nested_summary(self):
        arts = [{"title": "제목", "url": "http://x", "category": "그룹사", "summary": "요약본"}]
        html = format_clipboard_html(arts)
        self.assertIn('<a href="http://x"><strong>제목</strong></a>', html)
        self.assertIn("<ul><li>요약본</li></ul>", html)

    def test_footer_present(self):
        arts = [{"title": "제목", "url": "http://x", "category": "그룹사"}]
        self.assertIn(CLIPBOARD_FOOTER, format_clipboard_text(arts))
        self.assertIn("뉴스 클리핑 관련 의견", format_clipboard_html(arts))


if __name__ == "__main__":
    unittest.main()
