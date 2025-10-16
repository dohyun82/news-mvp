import unittest

from modules.curation import normalize_title, deduplicate, map_category, curate
from modules.config import get_default_keywords_by_category


class TestCuration(unittest.TestCase):
    def test_normalize_title(self):
        t = " [현대백화점그룹]  식권대장  협력   강화 "
        self.assertEqual(normalize_title(t), "현대백화점그룹 식권대장 협력 강화")

    def test_deduplicate(self):
        items = [
            {"title": "현대백화점그룹 협력 강화"},
            {"title": "현대백화점그룹   협력   강화"},
        ]
        result = deduplicate(items)
        self.assertEqual(len(result), 1)

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


