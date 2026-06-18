import unittest

from modules.curation import normalize_title, deduplicate, curate
from core.categories import UNCATEGORIZED


class TestCuration(unittest.TestCase):
    def test_normalize_title(self):
        t = " [현대백화점그룹]  식권대장  협력   강화 "
        self.assertEqual(normalize_title(t), "현대백화점그룹 식권대장 협력 강화")

    def test_deduplicate(self):
        # 제목 기반 중복 제거
        items = [
            {"title": "현대백화점그룹 협력 강화"},
            {"title": "현대백화점그룹   협력   강화"},
        ]
        self.assertEqual(len(deduplicate(items)), 1)

        # URL 기반 중복 제거 (같은 URL이면 중복)
        items_with_url = [
            {"title": "현대백화점그룹 협력 강화", "url": "http://example.com/1"},
            {"title": "다른 제목", "url": "http://example.com/1"},
        ]
        self.assertEqual(len(deduplicate(items_with_url)), 1)

        # 제목·URL 모두 다르면 유지
        items_different = [
            {"title": "현대백화점그룹 협력 강화", "url": "http://example.com/1"},
            {"title": "다른 제목", "url": "http://example.com/2"},
        ]
        self.assertEqual(len(deduplicate(items_different)), 2)

    def test_curate_assigns_uncategorized(self):
        raw = [
            {"title": "[광고] 최고의 프로모션 소식", "url": "http://x/ad"},
            {"title": "밀키트 수요 증가", "url": "http://x/1"},
            {"title": "밀키트 수요 증가", "url": "http://x/1-dup"},
        ]
        out = curate(raw)
        # 광고 제거 + 중복 제거로 1개만 남고, 카테고리는 미분류(분류는 검토 화면에서 수동)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["category"], UNCATEGORIZED)


if __name__ == "__main__":
    unittest.main()
