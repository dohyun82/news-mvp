import unittest
from unittest.mock import patch

from core.categories import UNCATEGORIZED


class TestIntegrationRealData(unittest.TestCase):
    @patch("modules.crawler._fetch_naver_news_api")
    @patch("modules.crawler.keyword_store")
    @patch("modules.crawler.RealDataConfig")
    def test_realdata_flow_curate(self, MockCfg, mock_keyword_store, mock_fetch):
        # RealDataConfig를 실데이터 경로로 설정
        cfg = MockCfg.return_value
        cfg.enabled = True
        cfg.client_id = "id"
        cfg.client_secret = "secret"
        cfg.timeout_ms = 3000
        cfg.sort = "sim"
        cfg.delay_ms = 0

        mock_keyword_store.get_query_keywords.return_value = "현대백화점"
        mock_keyword_store.get_max_articles.return_value = 5
        mock_keyword_store.get_max_age_hours.return_value = 0  # 나이 필터 비활성

        mock_fetch.return_value = [
            {"title": "<b>현대백화점</b> 그룹 협력 강화", "url": "http://news/1"},
            {"title": "<b>현대백화점</b> 그룹 협력 강화", "url": "http://news/1-dup"},
            {"title": "[광고] 최고의 프로모션", "url": "http://news/ad"},
        ]

        from modules.crawler import crawl_naver_news

        out = crawl_naver_news([])

        # 광고 제거 + 중복 제거 → 1개, 카테고리는 미분류(수동 분류 전)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["category"], UNCATEGORIZED)
        self.assertTrue(out[0]["title"].find("현대백화점") != -1)


if __name__ == "__main__":
    unittest.main()
