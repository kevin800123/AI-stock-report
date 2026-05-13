"""系統設定 Pydantic Schema。

Response 會遮蔽 Notion / OpenAI 等敏感設定值，避免經 API 外洩。
"""

from pydantic import BaseModel, ConfigDict, Field, model_validator


_SENSITIVE_KEYS = frozenset(
    {
        "notion_api_key",
        "notion_internal_integration_secret",
        "openai_api_key",
        "openai_api_secret",
    }
)


def is_sensitive_setting_key(key: str) -> bool:
    k = key.strip().lower()
    if k in _SENSITIVE_KEYS:
        return True
    return any(
        marker in k
        for marker in (
            "_secret",
            "_api_key",
            "_token",
            "_password",
            "api_secret",
        )
    )


class SettingUpsert(BaseModel):
    """新增或更新設定（寫入用；路由應限制為管理用途）。"""

    key: str = Field(..., max_length=128)
    value: str | None = None


class SettingUpdate(BaseModel):
    """依 key 更新 value。"""

    value: str | None = None


class SettingResponse(BaseModel):
    """設定 API 回應：`value` 在敏感鍵會被遮蔽為 None（不落實際 Secret）。"""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str | None

    @model_validator(mode="after")
    def redact_sensitive_values(self):
        if is_sensitive_setting_key(self.key):
            object.__setattr__(self, "value", None)
        return self


class SettingInternal(BaseModel):
    """僅供後端服務內部使用（勿直接回傳給前端）。"""

    model_config = ConfigDict(from_attributes=True)

    key: str
    value: str | None
