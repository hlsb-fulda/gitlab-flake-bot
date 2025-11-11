from dataclasses import dataclass
from typing import Optional

import munch

from .settings import RuleSettings
from .utils import match_any


@dataclass
class Input:
    project: str
    key: str
    name: str

    old: munch.Munch
    new: Optional[munch.Munch]

    def find_rule(self, rules: list[RuleSettings]) -> RuleSettings:
        for rule in rules:
            if not match_any(rule.projects, self.project):
                continue
            if not match_any(rule.inputs, self.key):
                continue

            return rule

        return RuleSettings()
