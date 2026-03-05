import unittest

from shared.integrations.slack import format_slack_message


class TestSlackDescriptionFallback(unittest.TestCase):
    def test_uses_description_when_summary_missing(self):
        articles = [
            {
                "title": "기사 A",
                "url": "https://example.com/a",
                "category": "그룹사",
                "summary": "",
                "description": "설명 기반 대체 텍스트",
            }
        ]

        msg = format_slack_message(articles)
        self.assertIn("<https://example.com/a|기사 A>", msg)
        self.assertIn("설명 기반 대체 텍스트", msg)

    def test_prefers_summary_over_description(self):
        articles = [
            {
                "title": "기사 B",
                "url": "https://example.com/b",
                "category": "업계",
                "summary": "요약 텍스트",
                "description": "설명 텍스트",
            }
        ]

        msg = format_slack_message(articles)
        self.assertIn("요약 텍스트", msg)
        self.assertNotIn("설명 텍스트", msg)

    def test_uses_description_when_summary_is_whitespace(self):
        articles = [
            {
                "title": "기사 C",
                "url": "https://example.com/c",
                "category": "참고",
                "summary": "   ",
                "description": "공백 요약 대체 설명",
            }
        ]

        msg = format_slack_message(articles)
        self.assertIn("공백 요약 대체 설명", msg)


if __name__ == "__main__":
    unittest.main()
