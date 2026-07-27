"""Shared Pydantic base model, used by every subproject's response schemas."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for API response models: snake_case in Python, camelCase over the wire.

    Keeps Python code idiomatic while matching the camelCase convention the
    TypeScript frontend uses for its own types.
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
