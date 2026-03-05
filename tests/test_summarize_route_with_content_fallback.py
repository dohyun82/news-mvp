import unittest
from unittest.mock import patch

from app import app
from apps.news.models import store
from shared.news.article_content_extractor import ExtractResult


class TestSummarizeRouteWithContentFallback(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        store.set_articles(
            [
                {
                    "title": "기사 A",
                    "url": "https://example.com/a",
                    "category": "그룹사",
                    "description": "기사 설명 A",
                }
            ]
        )

    def tearDown(self):
        store.set_articles([])

    @patch("apps.news.routes.get_summary_from_openai")
    @patch("apps.news.routes.extract_article_content")
    def test_uses_article_text_when_extraction_succeeds(self, mock_extract, mock_summary):
        mock_extract.return_value = ExtractResult(
            text="추출된 본문 내용",
            status="ok",
            source="trafilatura",
            error="",
        )
        mock_summary.return_value = "AI 요약 결과"

        response = self.client.post("/api/summarize", json={"url": "https://example.com/a"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["summary"], "AI 요약 결과")
        self.assertEqual(data["input_source"], "article_text")
        self.assertEqual(data["extract_status"], "ok")
        self.assertEqual(data["extract_source"], "trafilatura")
        self.assertEqual(data["summary_error"], "")

        _, kwargs = mock_summary.call_args
        self.assertEqual(kwargs["title"], "기사 A")
        self.assertEqual(kwargs["description"], "기사 설명 A")
        self.assertEqual(kwargs["article_text"], "추출된 본문 내용")

    @patch("apps.news.routes.get_summary_from_openai")
    @patch("apps.news.routes.extract_article_content")
    def test_falls_back_to_description_when_ai_summary_fails(self, mock_extract, mock_summary):
        mock_extract.return_value = ExtractResult(
            text="",
            status="blocked",
            source="fallback",
            error="HTTPError 403",
        )
        mock_summary.return_value = "https://example.com/a 요약 실패 (TimeoutError: timed out)"

        response = self.client.post("/api/summarize", json={"url": "https://example.com/a"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["summary"], "기사 설명 A")
        self.assertEqual(data["input_source"], "description")
        self.assertEqual(data["extract_status"], "blocked")
        self.assertEqual(data["extract_source"], "fallback")
        self.assertIn("요약 실패", data["summary_error"])

        saved = store.get_article_by_url("https://example.com/a")
        self.assertIsNotNone(saved)
        self.assertEqual(saved.summary, "기사 설명 A")

    @patch("apps.news.routes.get_summary_from_openai")
    @patch("apps.news.routes.extract_article_content")
    def test_returns_empty_summary_when_ai_fails_and_description_missing(self, mock_extract, mock_summary):
        store.set_articles(
            [
                {
                    "title": "기사 B",
                    "url": "https://example.com/b",
                    "category": "업계",
                }
            ]
        )
        mock_extract.return_value = ExtractResult(
            text="",
            status="parse_failed",
            source="fallback",
            error="parse failed",
        )
        mock_summary.return_value = "https://example.com/b 요약 실패 (RuntimeError: failure)"

        response = self.client.post("/api/summarize", json={"url": "https://example.com/b"})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data["summary"], "")
        self.assertEqual(data["input_source"], "title")
        self.assertIn("요약 실패", data["summary_error"])


if __name__ == "__main__":
    unittest.main()
