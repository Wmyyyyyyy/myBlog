import pytest
from core.moderation import DFAFilter, ModerationAction


class TestDFAFilter:
    def test_empty_word_list(self):
        filter = DFAFilter([])
        result = filter.check("hello world")
        assert result.passed is True
        assert result.action == "pass"

    def test_block_action(self):
        filter = DFAFilter([("bad", "block")])
        result = filter.check("this is bad content")
        assert result.passed is False
        assert result.action == "block"
        assert "b" in result.flagged_words or "a" in result.flagged_words or "d" in result.flagged_words

    def test_replace_action(self):
        filter = DFAFilter([("bad", "replace")])
        result = filter.check("this is bad content")
        assert result.passed is True
        assert result.action == "replace"
        assert "***" in result.moderated_text

    def test_warn_action(self):
        filter = DFAFilter([("bad", "warn")])
        result = filter.check("this is bad content")
        assert result.passed is True
        assert result.action == "warn"

    def test_multiple_flagged_words(self):
        filter = DFAFilter([("bad", "block"), ("evil", "replace")])
        result = filter.check("this is bad and evil")
        assert result.passed is False
        assert result.action == "block"
