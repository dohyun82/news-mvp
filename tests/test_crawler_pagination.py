import unittest
from unittest.mock import patch


class TestCrawlerPagination(unittest.TestCase):
    """start 페이지네이션이 동작하여 100건 초과 수집 시 중복이 생기지 않는지 검증."""

    @patch("modules.crawler._fetch_naver_news_api")
    @patch("modules.crawler.keyword_store")
    @patch("modules.crawler.RealDataConfig")
    def test_pagination_advances_start(self, MockCfg, mock_ks, mock_fetch):
        cfg = MockCfg.return_value
        cfg.enabled = True
        cfg.client_id = "id"
        cfg.client_secret = "secret"
        cfg.timeout_ms = 3000
        cfg.sort = "sim"
        cfg.delay_ms = 0
        cfg.log_each_item = False

        mock_ks.get_query_keywords.return_value = "현대백화점"
        mock_ks.get_max_articles.return_value = 250  # 100 초과 → 페이지네이션 필요
        mock_ks.get_max_age_hours.return_value = 0  # 나이 필터 비활성

        # start에 따라 서로 다른 고유 기사를 display 개수만큼 반환
        calls = []

        def fake_fetch(query, *, display, start, **kwargs):
            calls.append(start)
            return [
                {"title": f"t{start + i}", "url": f"http://n/{start + i}"}
                for i in range(display)
            ]

        mock_fetch.side_effect = fake_fetch

        from modules.crawler import crawl_naver_news

        out = crawl_naver_news([])

        # start가 1 → 101 → 201 로 전진해야 한다 (250 = 100+100+50)
        self.assertEqual(calls[:3], [1, 101, 201])
        # 페이지마다 고유 기사이므로 dedup 후에도 250건 모두 유지
        # (start 고정 버그였다면 같은 100건 반복 → dedup 후 100건으로 줄었을 것)
        self.assertEqual(len(out), 250)


if __name__ == "__main__":
    unittest.main()
