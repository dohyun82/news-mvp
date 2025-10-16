import unittest

from modules.slack import format_slack_message


class TestSlackFormatter(unittest.TestCase):
    def test_empty(self):
        msg = format_slack_message([])
        self.assertIn("선택된 기사가 없습니다.", msg)

    def test_grouping_and_links(self):
        arts = [
            {"title": "A", "url": "http://a", "category": "그룹사", "summary": "S1"},
            {"title": "B", "url": "http://b", "category": "업계", "summary": "S2"},
        ]
        msg = format_slack_message(arts)
        self.assertIn("*[그룹사]*", msg)
        self.assertIn("*[업계]*", msg)
        self.assertIn("<http://a|A>", msg)
        self.assertIn("— S1", msg)


if __name__ == "__main__":
    unittest.main()


