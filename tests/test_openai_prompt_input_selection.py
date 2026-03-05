import unittest
from types import SimpleNamespace
from unittest.mock import patch

from shared.ai.openai_client import get_summary_from_openai


class _DummyCompletions:
    def __init__(self, holder):
        self.holder = holder

    def create(self, **kwargs):
        self.holder["kwargs"] = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="요약 결과")
                )
            ]
        )


class _DummyOpenAI:
    holder = {}

    def __init__(self, *args, **kwargs):
        self.chat = SimpleNamespace(completions=_DummyCompletions(self.holder))


class TestOpenAIPromptInputSelection(unittest.TestCase):
    @patch("shared.ai.openai_client.OpenAIConfig")
    @patch("shared.ai.openai_client.OpenAI", _DummyOpenAI)
    def test_uses_article_text_when_available(self, mock_cfg):
        mock_cfg.return_value = SimpleNamespace(api_key="test-key")
        _DummyOpenAI.holder.clear()

        result = get_summary_from_openai(
            "https://example.com/a",
            title="기사 제목",
            description="메타 설명",
            article_text="본문 텍스트 내용",
        )

        self.assertEqual(result, "요약 결과")
        prompt = _DummyOpenAI.holder["kwargs"]["messages"][0]["content"]
        self.assertIn("[본문]", prompt)
        self.assertIn("본문 텍스트 내용", prompt)
        self.assertIn("입력에 없는 사실을 추측하거나 단정하지 말 것", prompt)

    @patch("shared.ai.openai_client.OpenAIConfig")
    @patch("shared.ai.openai_client.OpenAI", _DummyOpenAI)
    def test_falls_back_to_title_and_description_when_no_article_text(self, mock_cfg):
        mock_cfg.return_value = SimpleNamespace(api_key="test-key")
        _DummyOpenAI.holder.clear()

        result = get_summary_from_openai(
            "https://example.com/b",
            title="기사 제목 B",
            description="메타 설명 B",
            article_text=None,
        )

        self.assertEqual(result, "요약 결과")
        prompt = _DummyOpenAI.holder["kwargs"]["messages"][0]["content"]
        self.assertIn("[제목]", prompt)
        self.assertIn("기사 제목 B", prompt)
        self.assertIn("[요약문(description)]", prompt)
        self.assertIn("메타 설명 B", prompt)
        self.assertNotIn("[본문]", prompt)


if __name__ == "__main__":
    unittest.main()
