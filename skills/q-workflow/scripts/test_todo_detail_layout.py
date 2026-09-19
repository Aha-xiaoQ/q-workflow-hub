"""TODO detail comparisons preserve content while allowing Chinese clause wraps."""
import unittest

from workflow_stability_suite import normalize_detail_layout as suite_normalize
from base_command_surface_replay import normalize_detail_layout as replay_normalize


class TodoDetailLayoutCases:
    def test_unlabeled_sentences_and_repeated_punctuation(self):
        raw = "事项：保留版本。用户仍在制作。不要修改！准备好了吗？。下一步：等待。"
        wrapped = "事项：保留版本。\n   用户仍在制作。\n不要修改！\n准备好了吗？\n。\n下一步：等待。"
        self.assertEqual(self.normalize(raw), self.normalize(wrapped))

    def test_semicolon_fallback(self):
        self.assertEqual(self.normalize("保留副本；等待信号；继续"),
                         self.normalize("保留副本；\n等待信号；\n继续"))

    def test_labeled_sections_still_match(self):
        self.assertEqual(self.normalize("当前状态：等待。下一步：检查。完成条件：通过。"),
                         self.normalize("当前状态：等待。\n下一步：检查。\n完成条件：通过。"))

    def test_chat_header_boundary_is_preserved(self):
        chat = "已定位：demo / 示例\n详情：\n   事项：等待。\n   保留文件。"
        normalized = self.normalize(chat)
        self.assertIn("\n详情：\n", normalized)
        self.assertIn(self.normalize("事项：等待。保留文件。"), normalized)

    def test_non_clause_boundaries_are_not_erased(self):
        for wrapped, flattened in [("a\n b", "ab"), ("详情：\n事项", "详情：事项"),
                                   ("甲，\n乙", "甲，乙"), ("a.\nb", "a.b")]:
            with self.subTest(wrapped=wrapped):
                self.assertNotEqual(self.normalize(wrapped), self.normalize(flattened))

    def test_content_punctuation_order_and_internal_spaces_remain_significant(self):
        original = self.normalize("事项：先保留。\n下一步：等待信号。")
        for changed in ("", "事项：先保留。", "事项：先保留。下一步：等待",
                        "事项：先保留下一步：等待信号。", "事项：先保留！下一步：等待信号。",
                        "事项：先保留。下一步：执行。", "下一步：等待信号。事项：先保留。",
                        "事项：先 保留。下一步：等待信号。"):
            with self.subTest(changed=changed):
                self.assertNotEqual(original, self.normalize(changed))


class SuiteDetailLayoutTests(TodoDetailLayoutCases, unittest.TestCase):
    normalize = staticmethod(suite_normalize)


class ReplayDetailLayoutTests(TodoDetailLayoutCases, unittest.TestCase):
    normalize = staticmethod(replay_normalize)


if __name__ == "__main__":
    unittest.main()
