from pathlib import Path
from typing import Optional, Type, Tuple, Any
from datetime import timedelta

import pytimeparse2 as timeparse
from pydantic import (
    BaseModel,
    Field,
    GetCoreSchemaHandler,
)
from pydantic_core import core_schema
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, TomlConfigSettingsSource, CliApp


class Duration(timedelta):
    @classmethod
    def __get_pydantic_core_schema__(cls, source: type[Any], handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            lambda s: timeparse.parse(s, raise_exception=True, as_timedelta=True),
            core_schema.str_schema(min_length=1),
        )


class GitLabSettings(BaseSettings):
    url: str = Field(default="https://gitlab.com")
    api_token: Optional[str] = Field(default=None)


class RuleSettings(BaseModel):
    projects: list[str] = Field(default=["*"])
    inputs: list[str] = Field(default=["*"])

    ignore: bool = Field(default=False)

    interval: Optional[Duration] = Field(default=None)
    auto_merge: Optional[bool] = Field(default=None)


class Settings(BaseSettings):
    gitlab: GitLabSettings = Field(default_factory=GitLabSettings)

    cache: Path = Field(default="/var/cache/gitlab-flake-bot")

    interval: Optional[Duration] = Field(default="5min")

    projects: list[str] = Field(default=["*"])
    rules: list[RuleSettings] = Field(default_factory=list)

    commit_message: str = Field()
    branch_prefix: str = Field(default="deps/")
    auto_merge: bool = Field(default=False)

    model_config = SettingsConfigDict(toml_file="config.toml")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (TomlConfigSettingsSource(settings_cls),)


settings = CliApp.run(Settings)
