import os
import shutil
import tempfile
import unittest

from apps.news.models import InMemoryStore
from core.categories import UNCATEGORIZED


class TestStoreSelection(unittest.TestCase):
    """InMemoryStore.set_selected 의 선택 해제 동작 검증."""

    def setUp(self):
        # 실제 데이터 파일을 건드리지 않도록 임시 디렉터리의 미존재 경로 사용
        self._tmpdir = tempfile.mkdtemp()
        path = os.path.join(self._tmpdir, "articles.json")
        self.store = InMemoryStore(persist_path=path)
        self.store.set_articles([
            {
                "title": "T",
                "url": "http://x",
                "category": UNCATEGORIZED,
                "description": "네이버 요약",
            },
        ])

    def tearDown(self):
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _setup_summarized(self):
        """카테고리 분류 + 선택 + AI 요약까지 된 상태로 만든다."""
        self.store.set_category("http://x", "그룹사")
        self.store.set_selected("http://x", True)
        self.store.set_summary("http://x", "AI 요약 텍스트")

    def test_deselect_resets_ai_summary(self):
        # 선택 해제 시 AI 요약은 리셋된다
        self._setup_summarized()
        self.store.set_selected("http://x", False)
        a = self.store.get_article_by_url("http://x")
        self.assertEqual(a.summary, "")

    def test_deselect_keeps_naver_description(self):
        # 네이버 요약(description)은 선택 해제 후에도 유지된다
        self._setup_summarized()
        self.store.set_selected("http://x", False)
        a = self.store.get_article_by_url("http://x")
        self.assertEqual(a.description, "네이버 요약")

    def test_deselect_restores_original_category(self):
        # 선택 해제 시 원본 카테고리(미분류)로 복원된다
        self._setup_summarized()
        self.store.set_selected("http://x", False)
        a = self.store.get_article_by_url("http://x")
        self.assertEqual(a.category, UNCATEGORIZED)

    def test_select_keeps_summary(self):
        # 선택(True) 시에는 AI 요약을 건드리지 않는다
        self._setup_summarized()
        a = self.store.get_article_by_url("http://x")
        self.assertEqual(a.summary, "AI 요약 텍스트")


if __name__ == "__main__":
    unittest.main()
