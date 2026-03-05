import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shared.news.article_content_extractor import extract_article_content


class _DummyHeaders:
    def get_content_charset(self):
        return "utf-8"


class _DummyResponse:
    def __init__(self, body: str):
        self._body = body.encode("utf-8")
        self.headers = _DummyHeaders()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class TestArticleContentExtractor(unittest.TestCase):
    @patch("shared.news.article_content_extractor.urllib.request.urlopen")
    @patch("shared.news.article_content_extractor.ArticleFetchConfig")
    @patch("shared.news.article_content_extractor.trafilatura")
    def test_extract_success_with_trafilatura(self, mock_trafilatura, mock_cfg, mock_urlopen):
        mock_cfg.return_value = SimpleNamespace(enabled=True, timeout_seconds=5, text_max_chars=4000)
        mock_urlopen.return_value = _DummyResponse("<html><body><p>raw</p></body></html>")
        mock_trafilatura.extract.return_value = "본문 추출 결과\n\n추가 줄"

        result = extract_article_content("https://example.com/news")

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.source, "trafilatura")
        self.assertIn("본문 추출 결과", result.text)

    @patch("shared.news.article_content_extractor.urllib.request.urlopen")
    @patch("shared.news.article_content_extractor.ArticleFetchConfig")
    def test_extract_timeout(self, mock_cfg, mock_urlopen):
        mock_cfg.return_value = SimpleNamespace(enabled=True, timeout_seconds=5, text_max_chars=4000)
        mock_urlopen.side_effect = TimeoutError("timed out")

        result = extract_article_content("https://example.com/news")
        self.assertEqual(result.status, "timeout")
        self.assertEqual(result.text, "")

    @patch("shared.news.article_content_extractor.urllib.request.urlopen")
    @patch("shared.news.article_content_extractor.ArticleFetchConfig")
    @patch("shared.news.article_content_extractor.trafilatura")
    def test_extract_empty_when_no_readable_text(self, mock_trafilatura, mock_cfg, mock_urlopen):
        mock_cfg.return_value = SimpleNamespace(enabled=True, timeout_seconds=5, text_max_chars=4000)
        mock_urlopen.return_value = _DummyResponse("<html><body><script>var a=1;</script></body></html>")
        mock_trafilatura.extract.return_value = ""

        result = extract_article_content("https://example.com/news")
        self.assertEqual(result.status, "empty")
        self.assertEqual(result.source, "fallback")

    @patch("shared.news.article_content_extractor.urllib.request.urlopen")
    @patch("shared.news.article_content_extractor.ArticleFetchConfig")
    @patch("shared.news.article_content_extractor.trafilatura")
    def test_extract_respects_max_chars(self, mock_trafilatura, mock_cfg, mock_urlopen):
        mock_cfg.return_value = SimpleNamespace(enabled=True, timeout_seconds=5, text_max_chars=10)
        mock_urlopen.return_value = _DummyResponse("<html><body>raw</body></html>")
        mock_trafilatura.extract.return_value = "가나다라마바사아자차카타"

        result = extract_article_content("https://example.com/news")
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(result.text), 10)


if __name__ == "__main__":
    unittest.main()
