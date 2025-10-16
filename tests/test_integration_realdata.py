import unittest
from unittest.mock import patch


class TestIntegrationRealData(unittest.TestCase):
    @patch("modules.crawler._fetch_naver_news_api")
    @patch("modules.config.RealDataConfig")
    def test_realdata_flow_curate_and_category(self, MockCfg, mock_fetch):
        # Configure RealDataConfig to enable realdata path
        cfg = MockCfg.return_value
        cfg.enabled = True
        cfg.client_id = "id"
        cfg.client_secret = "secret"
        cfg.query_keywords = "현대백화점"
        cfg.max_articles = 5
        cfg.timeout_ms = 3000
        cfg.sort = "sim"
        cfg.delay_ms = 0

        # Mock API response items
        mock_fetch.return_value = [
            {"title": "<b>현대백화점</b> 그룹 협력 강화", "url": "http://news/1"},
            {"title": "<b>현대백화점</b> 그룹 협력 강화", "url": "http://news/1-dup"},
            {"title": "[광고] 최고의 프로모션", "url": "http://news/ad"},
        ]

        from modules.crawler import crawl_naver_news

        out = crawl_naver_news([])

        # 광고 제거 + 중복 제거 → 1개만 남고, 그룹사 카테고리로 매핑되어야 함
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["category"], "그룹사")
        self.assertTrue(out[0]["title"].find("현대백화점") != -1)


if __name__ == "__main__":
    unittest.main()


