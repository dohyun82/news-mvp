import unittest

from modules.curation import normalize_title, deduplicate, map_category, curate
from modules.config import get_default_keywords_by_category


class TestCuration(unittest.TestCase):
    def test_normalize_title(self):
        t = " [현대백화점그룹]  식권대장  협력   강화 "
        self.assertEqual(normalize_title(t), "현대백화점그룹 식권대장 협력 강화")

    def test_deduplicate(self):
        # 제목 기반 중복 제거 테스트
        items = [
            {"title": "현대백화점그룹 협력 강화"},
            {"title": "현대백화점그룹   협력   강화"},
        ]
        result = deduplicate(items)
        self.assertEqual(len(result), 1)
        
        # URL 기반 중복 제거 테스트
        items_with_url = [
            {"title": "현대백화점그룹 협력 강화", "url": "http://example.com/1"},
            {"title": "다른 제목", "url": "http://example.com/1"},  # 같은 URL, 다른 제목
        ]
        result = deduplicate(items_with_url)
        self.assertEqual(len(result), 1)  # URL이 같으므로 중복으로 처리
        
        # 제목과 URL 모두 다른 경우 (중복 아님)
        items_different = [
            {"title": "현대백화점그룹 협력 강화", "url": "http://example.com/1"},
            {"title": "다른 제목", "url": "http://example.com/2"},  # 다른 URL, 다른 제목
        ]
        result = deduplicate(items_different)
        self.assertEqual(len(result), 2)  # 둘 다 유지

    def test_map_category(self):
        kws = get_default_keywords_by_category()
        cat = map_category("기업 복지 포인트 확대", kws)
        self.assertEqual(cat, "업계")

    def test_curate_pipeline(self):
        kws = get_default_keywords_by_category()
        raw = [
            {"title": "[광고] 최고의 프로모션 소식", "url": "http://x/ad"},
            {"title": "밀키트 수요 증가", "url": "http://x/1"},
            {"title": "밀키트 수요 증가", "url": "http://x/1-dup"},
        ]
        out = curate(raw, kws)
        # 광고 제거 + 중복 제거로 1개만 남음
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["category"], "업계")


if __name__ == "__main__":
    unittest.main()


