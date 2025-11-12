import tomllib
from datetime import timedelta
from pathlib import Path
from typing import Optional, Any

import pydantic_core
import pytimeparse2 as timeparse
from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
)


class Duration(timedelta):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler):
        return pydantic_core.core_schema.no_info_after_validator_function(
            cls._validate,
            pydantic_core.core_schema.str_schema(min_length=1),
        )

    @classmethod
    def _validate(cls, v: Any) -> timedelta:
        if isinstance(v, timedelta):
            return v

        if isinstance(v, (int, float)):
            return timedelta(seconds=v)

        if isinstance(v, str):
            return timeparse.parse(v, raise_exception=True, as_timedelta=True)

        raise ValueError(f"Invalid duration type: {type(v).__name__!r} (expected timedelta, int, float, or str)")


class GitLabSettings(BaseModel):
    url: str = Field(default="https://gitlab.com")
    api_token: Optional[str] = Field(default=None)


class RuleSettings(BaseModel):
    projects: list[str] = Field(default=["*"])
    inputs: list[str] = Field(default=["*"])

    ignore: bool = Field(default=False)

    interval: Optional[Duration] = Field(default=None)
    auto_merge: Optional[bool] = Field(default=None)


class Settings(BaseModel):
    gitlab: GitLabSettings = Field(default_factory=GitLabSettings)

    cache: Path = Field(default="/var/cache/gitlab-flake-bot")

    interval: Optional[Duration] = Field(default=None)

    projects: list[str] = Field(default=["*"])
    rules: list[RuleSettings] = Field(default_factory=list)

    commit_message: str = Field()
    branch_prefix: str = Field(default="deps/")
    auto_merge: bool = Field(default=False)


class DeferredSettings(object):
    def __init__(self):
        self.__settings = None

    def load(self, path: Path):
        with path.open("rb") as f:
            config = tomllib.load(f)
            config = Settings.model_validate(config)

        self.__settings = config

    def __getattr__(self, name):
        return getattr(self.__settings, name)


settings = DeferredSettings()
