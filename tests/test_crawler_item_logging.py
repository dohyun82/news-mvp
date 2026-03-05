import unittest
from unittest.mock import MagicMock, patch

from modules.crawler import crawl_naver_news


class TestCrawlerItemLogging(unittest.TestCase):
    @patch("modules.crawler.logging.getLogger")
    @patch("modules.crawler._fetch_naver_news_api")
    @patch("modules.crawler.keyword_store")
    @patch("modules.crawler.RealDataConfig")
    def test_logs_each_item_when_enabled(self, MockCfg, mock_keyword_store, mock_fetch, mock_get_logger):
        cfg = MockCfg.return_value
        cfg.enabled = True
        cfg.client_id = "id"
        cfg.client_secret = "secret"
        cfg.timeout_ms = 3000
        cfg.sort = "sim"
        cfg.delay_ms = 0
        cfg.log_each_item = True

        mock_keyword_store.get_query_keywords.return_value = "테스트키워드"
        mock_keyword_store.get_max_articles.return_value = 2
        mock_keyword_store.get_max_age_hours.return_value = 0
        mock_keyword_store.get_category_keywords.return_value = {
            "그룹사": [],
            "업계": [],
            "참고": [],
        }

        mock_fetch.return_value = [
            {
                "title": "기사 제목 1",
                "url": "https://example.com/1",
                "description": "설명 1",
                "pub_date": "Thu, 13 Nov 2025 16:56:00 +0900",
            },
            {
                "title": "기사 제목 2",
                "url": "https://example.com/2",
                "description": "설명 2",
                "pub_date": "Thu, 13 Nov 2025 16:57:00 +0900",
            },
        ]

        logger = MagicMock()
        mock_get_logger.return_value = logger

        out = crawl_naver_news([])
        self.assertEqual(len(out), 2)

        item_logs = [
            call
            for call in logger.info.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("fetched item")
        ]
        self.assertEqual(len(item_logs), 2)

    @patch("modules.crawler.logging.getLogger")
    @patch("modules.crawler._fetch_naver_news_api")
    @patch("modules.crawler.keyword_store")
    @patch("modules.crawler.RealDataConfig")
    def test_does_not_log_each_item_when_disabled(self, MockCfg, mock_keyword_store, mock_fetch, mock_get_logger):
        cfg = MockCfg.return_value
        cfg.enabled = True
        cfg.client_id = "id"
        cfg.client_secret = "secret"
        cfg.timeout_ms = 3000
        cfg.sort = "sim"
        cfg.delay_ms = 0
        cfg.log_each_item = False

        mock_keyword_store.get_query_keywords.return_value = "테스트키워드"
        mock_keyword_store.get_max_articles.return_value = 1
        mock_keyword_store.get_max_age_hours.return_value = 0
        mock_keyword_store.get_category_keywords.return_value = {
            "그룹사": [],
            "업계": [],
            "참고": [],
        }

        mock_fetch.return_value = [
            {
                "title": "기사 제목 1",
                "url": "https://example.com/1",
                "description": "설명 1",
                "pub_date": "Thu, 13 Nov 2025 16:56:00 +0900",
            }
        ]

        logger = MagicMock()
        mock_get_logger.return_value = logger

        out = crawl_naver_news([])
        self.assertEqual(len(out), 1)

        item_logs = [
            call
            for call in logger.info.call_args_list
            if call.args and isinstance(call.args[0], str) and call.args[0].startswith("fetched item")
        ]
        self.assertEqual(len(item_logs), 0)


if __name__ == "__main__":
    unittest.main()
