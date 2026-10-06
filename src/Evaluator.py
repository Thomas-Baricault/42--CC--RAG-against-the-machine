from typing import List
from .models import AnsweredQuestion, MinimalAnswer, MinimalSource


class Evaluator:
    """Class to evaluate recall at k score

    Attributes
    ----------
    MIN_OVERLAP : int
        The minimum overlaping ratio to consider the file found

    Static Methods
    --------------
    recall_at_k(retrieved, ground_truth, k) -> float
        Returns the recall@k score for a question
    """

    MIN_OVERLAP = 0.05

    @staticmethod
    def recall_at_k(retrieved: MinimalAnswer, ground_truth: AnsweredQuestion,
                    k: int) -> float:
        """Returns the recall@k score for a question

        Parameters
        ----------
        retrieved : MinimalAnswer
            The retrieved answer
        ground_truth : AnsweredQuestion
            The reference answer
        k : int
            The number of sources to use

        Returns
        -------
        float
            The recall@k score

        Raises
        ------
        Exception
            If k is less than 1
        """

        if k < 1:
            raise Exception("k must be greater or equal to 1")
        n = 0
        for gt in ground_truth.sources:
            if Evaluator._source_found(retrieved.retrieved_sources[:k], gt):
                n += 1
        return n / len(ground_truth.sources) if ground_truth.sources else 1

    @staticmethod
    def _source_found(retrieved: List[MinimalSource],
                      ground_truth: MinimalSource) -> bool:
        for r in retrieved:
            if Evaluator._overlap(r, ground_truth) >= Evaluator.MIN_OVERLAP:
                return True
        return False

    @staticmethod
    def _overlap(a: MinimalSource, b: MinimalSource) -> float:
        if a.file_path != b.file_path:
            return 0
        start = max(a.first_character_index, b.first_character_index)
        end = min(a.last_character_index, b.last_character_index)
        if end < start:
            return 0
        if b.last_character_index == b.first_character_index - 1:
            return 0
        return ((end - start + 1) /
                (b.last_character_index - b.first_character_index + 1))
