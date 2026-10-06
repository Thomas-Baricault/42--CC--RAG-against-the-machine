from bm25s import BM25, tokenize
from json import load
from os.path import join
from .models import MinimalSearchResults, MinimalSource, UnansweredQuestion


class Retriever:
    """Class to retrieve sources for a question

    Methods
    -------
    retrieve(question, k) -> MinimalSearchResults
        Retrieve sources from a question
    """

    def __init__(self, folder: str) -> None:
        """
        Parameters
        ----------
        folder : str
            The folder from which to load indexed data
        """

        self._bm25s = BM25.load(join(folder, "bm25_index"), load_corpus=False)
        with open(join(folder, "chunks/chunks.json"), "r") as file:
            self._bm25s.corpus = [MinimalSource(**src) for src in load(file)]

    def retrieve(self, question: UnansweredQuestion,
                 k: int) -> MinimalSearchResults:
        """Retrieve sources from a question

        Parameters
        ----------
        question: UnansweredQuestion
            The question
        k : int
            The number of sources to retrieve for each question

        Raises
        ------
        Exception
            If k is less than 1
        """

        if k < 1:
            raise Exception("k must be greater or equal to 1")
        return MinimalSearchResults(
            **question.model_dump(),
            retrieved_sources=self._bm25s.retrieve(tokenize(question.question),
                                                   k=k)[0][0]
        )
