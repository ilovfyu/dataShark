from typing import Dict
from pydantic import Field
from backend.dto.base import BaseSchema


class K8SConfigBase(BaseSchema):
    labels: Dict[str, str] = Field(default=None, description="标签")