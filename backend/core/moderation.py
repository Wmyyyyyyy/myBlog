from enum import Enum
from dataclasses import dataclass


class ModerationAction(str, Enum):
    BLOCK = "block"
    REPLACE = "replace"
    WARN = "warn"


@dataclass
class ModerationResult:
    passed: bool
    action: str
    original_text: str
    moderated_text: str | None
    flagged_words: list[str]

    @property
    def block(self) -> bool:
        return self.action == ModerationAction.BLOCK.value

    @property
    def replace(self) -> bool:
        return self.action == ModerationAction.REPLACE.value


class DFAFilter:
    def __init__(self, word_list: list[tuple[str, str]]):
        self._fail_state = -1
        self._next_state = 1
        self._goto = [{0: {}}]
        self._output = [None]
        self._states = [0]

        sorted_words = sorted(word_list, key=lambda x: len(x[0]), reverse=True)
        for word, action in sorted_words:
            self._add_word(word, action)

    def _add_word(self, word: str, action: str) -> None:
        state = 0
        for char in word.lower():
            if char not in self._goto[state]:
                new_state = self._next_state
                self._next_state += 1
                self._goto[state][char] = new_state
                self._goto.append({})
                self._output.append(None)
                self._states.append(new_state)
                state = new_state
            else:
                state = self._goto[state][char]
        self._output[state] = action

    def check(self, text: str) -> ModerationResult:
        if not self._goto[0]:
            return ModerationResult(
                passed=True,
                action="pass",
                original_text=text,
                moderated_text=text,
                flagged_words=[],
            )

        flagged = []
        result_text = list(text)
        highest_action_priority = 0

        i = 0
        while i < len(text):
            char = text[i].lower()
            if char not in self._goto[0]:
                i += 1
                continue

            state = self._goto[0].get(char, self._fail_state)
            match_end = i
            matched_action = None

            j = i + 1
            while state != self._fail_state and j < len(text):
                char_next = text[j].lower()
                if char_next in self._goto[state]:
                    state = self._goto[state][char_next]
                    match_end = j
                    if self._output[state] is not None:
                        matched_action = self._output[state]
                    j += 1
                else:
                    break

            if matched_action is not None:
                flagged.extend([text[k] for k in range(i, match_end + 1)])
                action_priority = {"warn": 1, "replace": 2, "block": 3}.get(matched_action, 0)
                if action_priority > highest_action_priority:
                    highest_action_priority = action_priority
                    for k in range(i, match_end + 1):
                        result_text[k] = "*"

            i += 1

        flagged_unique = list(set("".join(flagged)))
        action_map = {3: "block", 2: "replace", 1: "warn", 0: "pass"}
        final_action = action_map.get(highest_action_priority, "pass")

        return ModerationResult(
            passed=final_action != "block",
            action=final_action,
            original_text=text,
            moderated_text="".join(result_text) if final_action in ("replace", "pass") else None,
            flagged_words=flagged_unique,
        )


_default_filter: DFAFilter | None = None


def get_filter() -> DFAFilter:
    global _default_filter
    if _default_filter is None:
        _default_filter = DFAFilter([])
    return _default_filter


def reload_filter(word_list: list[tuple[str, str]]) -> DFAFilter:
    global _default_filter
    _default_filter = DFAFilter(word_list)
    return _default_filter
