from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List
from uuid import uuid4
from .utils import load_json


class MinimalSource(BaseModel):
    """Representation of a minimal source of information"""

    file_path: str
    first_character_index: int = Field(ge=0)
    last_character_index: int = Field(ge=0)


class MinimalSearchResults(BaseModel):
    """Representation of a search result"""

    question_id: str
    question: str
    retrieved_sources: List[MinimalSource]


class MinimalAnswer(MinimalSearchResults):
    """Representation of an answer"""

    answer: str


class StudentSearchResults(BaseModel):
    """Representation of the search results"""

    search_results: List[MinimalSearchResults]
    k: int = Field(gt=0)


class StudentSearchResultsAndAnswer(BaseModel):
    """Representation of the answered search results"""

    search_results: List[MinimalAnswer]
    k: int = Field(gt=0)


class UnansweredQuestion(BaseModel):
    """Representation of an unanswered question"""

    question_id: str = Field(default_factory=lambda: str(uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """Representation of an answered question"""

    sources: List[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Representation of a dataset of RAG questions"""

    rag_questions: List[AnsweredQuestion] | List[UnansweredQuestion]

    @classmethod
    def load(cls, path: str, answered: bool) -> RagDataset:
        return RagDataset(rag_questions=[
            AnsweredQuestion(**data) if answered else
            UnansweredQuestion(**data)
            for data in load_json(path)["rag_questions"]
        ])
