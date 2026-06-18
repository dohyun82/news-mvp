import unittest

from modules.curation import normalize_title, normalize_url, deduplicate, curate, dedupe_keywords
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

    def test_normalize_title_strips_format_lead_tags(self):
        # 형식 말머리([속보] 등)는 제거하되 주체명 말머리는 보존한다
        self.assertEqual(normalize_title("[속보] 실적 발표"), "실적 발표")
        self.assertEqual(normalize_title("[종합2보] 실적 발표"), "실적 발표")
        self.assertEqual(normalize_title("[단독][영상] 인터뷰"), "인터뷰")
        self.assertEqual(normalize_title("[현대백화점그룹] 협력"), "현대백화점그룹 협력")

    def test_normalize_url(self):
        # www/m·scheme·끝슬래시·추적파라미터·fragment 정규화
        self.assertEqual(normalize_url("http://www.a.com/1/"), "https://a.com/1")
        self.assertEqual(normalize_url("http://m.a.com/x"), "https://a.com/x")
        self.assertEqual(
            normalize_url("https://a.com/1?utm_source=naver&id=5"),
            "https://a.com/1?id=5",
        )
        # 쿼리 ID는 보존하여 같은 사이트의 다른 기사를 구분한다
        self.assertNotEqual(
            normalize_url("https://a.com/v?idxno=1"),
            normalize_url("https://a.com/v?idxno=2"),
        )

    def test_deduplicate_url_variants(self):
        # http/https·www·끝슬래시만 다른 같은 기사 → 1개로 합쳐짐
        items = [
            {"title": "서로 다른 제목 A", "url": "http://www.x.com/1"},
            {"title": "서로 다른 제목 B", "url": "https://x.com/1/"},
        ]
        self.assertEqual(len(deduplicate(items)), 1)

    def test_deduplicate_lead_tag_variants(self):
        # 형식 말머리만 다른 같은 기사 → 1개로 합쳐짐 (URL은 서로 다름)
        items = [
            {"title": "[속보] 현대백화점 호조", "url": "http://x.com/1"},
            {"title": "현대백화점 호조", "url": "http://y.com/2"},
        ]
        self.assertEqual(len(deduplicate(items)), 1)

    def test_dedupe_keywords(self):
        # (A) 표기 변형(공백) 제거 — 첫 등장만 유지
        self.assertEqual(dedupe_keywords(["배달앱", "배달 앱"]), ["배달앱"])
        # (B) 포함관계 하위어 제거 — 짧은 상위어만 유지
        self.assertEqual(dedupe_keywords(["벤디스", "현대벤디스"]), ["벤디스"])
        self.assertEqual(
            dedupe_keywords(["스타트업", "스타트업 투자", "스타트업 인수"]),
            ["스타트업"],
        )
        # 독립 키워드는 보존하고 순서를 유지
        self.assertEqual(
            dedupe_keywords(["식권대장", "복지대장"]), ["식권대장", "복지대장"]
        )
        # 빈 문자열·공백은 제거
        self.assertEqual(dedupe_keywords(["", "  ", "토스"]), ["토스"])


if __name__ == "__main__":
    unittest.main()
