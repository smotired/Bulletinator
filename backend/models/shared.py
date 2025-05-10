"""Request and response models for shared functionality."""

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, model_validator
from backend.database.schema import Base

class BadRequest(BaseModel):
    """Response model for error messages."""
    
    error: str
    message: str
    
class Metadata(BaseModel):
    """Used in response models for collections. May have more fields later."""

    count: int

class Collection[content_model](BaseModel):
    """Internal model for a generic collection."""
    metadata: Metadata
    contents: list[content_model]
    
# Factory for a generic collection with a validator
def CollectionFactory(content_model: type[BaseModel], db_model: type[Base]) -> type[BaseModel]: # type: ignore
    class Collection(BaseModel):
        metadata: Metadata
        contents: list[content_model] # type: ignore

        @model_validator(mode='before')
        @classmethod
        def convert_db_list(cls, obj: Any) -> Any:
            """Constructs a collection from a list of the equivalent db_model"""
            if isinstance(obj, list):
                # Make sure either the list is empty or everything matches this type
                if not all([ isinstance(x, db_model) for x in obj ]):
                    return obj
                # If this is indeed a list[DBType] create the equivalent of a Collection[ContentsType] from these items
                return cls(
                    metadata=Metadata( count=len(obj) ),
                    contents=[ content_model.model_validate(element.__dict__) for element in obj ]
                ).model_dump()
            return obj
    return Collection

class Success(BaseModel):
    """Response model for a very basic success."""
    status: str = "success"