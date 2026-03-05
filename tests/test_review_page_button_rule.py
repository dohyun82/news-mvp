import unittest

from app import app


class TestReviewPageButtonRule(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    def test_news_review_page_uses_summary_independent_send_rule(self):
        response = self.client.get("/news/review")
        self.assertEqual(response.status_code, 200)

        html = response.get_data(as_text=True)
        self.assertIn(
            "sendSlackBtn.disabled = selectedNews.length === 0;",
            html,
        )
        self.assertNotIn(
            "sendSlackBtn.disabled = !allSummarized || selectedNews.length === 0;",
            html,
        )
        self.assertNotIn("const allSummarized =", html)

    def test_legacy_review_route_redirects_to_news_review(self):
        response = self.client.get("/review", follow_redirects=False)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.headers.get("Location"), "/news/review")


if __name__ == "__main__":
    unittest.main()
