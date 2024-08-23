from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """
    Using extra keyword arguments on `Field` is deprecated and will be removed. Use `json_schema_extra` instead. (Extra keys: 'example').
    """
    # title: Optional[str] = Field(None, example="クリーニングを取りに行く")
    title: Optional[str] = Field(None)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "クリーニングを取りに行く",
                }
            ]
        }
    }


class TaskCreate(TaskBase):
    pass


class TaskCreateResponse(TaskBase):
    id: int

    """
    Support for class-based `config` is deprecated, use ConfigDict instead.
    """
    """
    Valid config keys have changed in V2:
    * 'orm_mode' has been renamed to 'from_attributes'
    """
    # class Config:
    #     orm_mode = True
    model_config = ConfigDict(
        from_attributes=True,
    )


class Task(TaskBase):
    id: int
    done: bool = Field(False, description="完了フラグ")

    model_config = ConfigDict(
        from_attributes=True,
    )
