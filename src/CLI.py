from fire import Fire
from os import makedirs
from tqdm import tqdm
from typing import Dict, List
from .Evaluator import Evaluator
from .Indexer import Indexer
from .LLM import LLM
from .Retriever import Retriever
from .models import (RagDataset, StudentSearchResults,
                     StudentSearchResultsAndAnswer, UnansweredQuestion)
from .utils import dump_json, load_json, new_file_path, print_json


class CLI:
    """Representation of the project CLI

    Methods
    -------
    index(max_chunk_size) -> None
        Index the repository
    search(query, k) -> None
        Search for a single query
    search_dataset(dataset_path, k, save_directory) -> None
        Process multiple questions and output search results
    answer(query, k) -> None
        Answer a single question with context
    answer_dataset(student_search_results_path, save_directory) -> None
        Generate answers from search results
    evaluate(dataset_path, student_search_results_path) -> None
        Evaluate search results against ground truth
    """

    def __init__(self) -> None:
        Fire(self)

    def index(self, max_chunk_size: int = 2000) -> None:
        """Index the repository

        Parameters
        ----------
        max_chunk_size : int
            The maximum size of a source chunk of data (default is 2000)
        """

        raw_path = "data/raw"
        processed_path = "data/processed"
        print(f"Indexing content of '{raw_path}'")
        print(f"MAX_CHUNK_SIZE = {max_chunk_size}")
        print()
        with tqdm(desc="Initializing indexer", total=3) as bar:
            indexer = Indexer(max_chunk_size)
            bar.desc = "Indexing raw data"
            bar.update()
            indexer.index(raw_path)
            bar.desc = "Saving indexed data"
            bar.update()
            indexer.save(processed_path)
            bar.update()
        print()
        print(f"Index saved at '{processed_path}'")

    def search(self, query: str, k: int = 10) -> None:
        """Search for a single query

        Parameters
        ----------
        query : str
            The query
        k : int
            The number of sources to retrieve
        """

        print(f"Searching for '{query}'")
        print(f"K = {k}")
        print()
        with tqdm(desc="Loading retriever", total=2) as bar:
            retriever = Retriever("data/processed")
            bar.desc = "Retrieving sources"
            bar.update()
            results = retriever.retrieve(UnansweredQuestion(question=query), k)
            bar.update()
        print()
        print_json(StudentSearchResults(k=k, search_results=[results]))

    def search_dataset(self,
                       dataset_path: str = "data/datasets/UnansweredQuestions/"
                                           + "dataset_docs_public.json",
                       k: int = 10,
                       save_directory: str = "data/output/search_results"
                       ) -> None:
        """Process multiple questions and output search results

        Parameters
        ----------
        dataset_path : str
            The questions dataset path
        k : int
            The number of sources to retrieve per search
        save_directory : str
            The directory in which create the output file
        """

        print(f"Searching for dataset '{dataset_path}'")
        print(f"K = {k}")
        print()
        with tqdm(desc="Loading dataset", total=2) as bar:
            dataset = RagDataset.load(dataset_path, False)
            bar.desc = "Loading retriever"
            bar.update()
            retriever = Retriever("data/processed")
            bar.update()
        results = [retriever.retrieve(question, k)
                   for question in tqdm(dataset.rag_questions,
                                        desc="Retrieving sources")]
        with tqdm(desc="Saving search results", total=1) as bar:
            makedirs(save_directory, exist_ok=True)
            dump_json(new_file_path(dataset_path, save_directory),
                      StudentSearchResults(k=k, search_results=results))
            bar.update()
        print()
        print(f"Search results saved at '{save_directory}'")

    def answer(self, query: str, k: int = 10) -> None:
        """Answer a single question with context

        Parameters
        ----------
        query : str
            The query to answer
        k : int
            The number of sources representing the context (default is 10)
        """

        print(f"Answer query '{query}'")
        print(f"K = {k}")
        print()
        with tqdm(desc="Loading retriever", total=4) as bar:
            retriever = Retriever("data/processed")
            bar.desc = "Retrieving sources"
            bar.update()
            results = retriever.retrieve(UnansweredQuestion(question=query), k)
            bar.desc = "Loading LLM"
            bar.update()
            llm = LLM()
            bar.desc = "Generating answer"
            bar.update()
            answer = llm.generate(results)
            bar.update()
        print()
        print_json(StudentSearchResultsAndAnswer(k=k, search_results=[answer]))

    def answer_dataset(self,
                       student_search_results_path: str = (
                           "data/output/search_results/"
                           + "dataset_docs_public.json"),
                       save_directory: str = "data/output/"
                                             + "search_results_and_answer"
                       ) -> None:
        """Generate answers from search results

        Parameters
        ----------
        student_search_results_path : str
            The search results file path
        save_directory : str
            The directory in which create the output file
        """

        print(f"Answer search results '{student_search_results_path}'")
        print()
        with tqdm(desc="Loading search results", total=2) as bar:
            search_results = StudentSearchResults(**load_json(
                student_search_results_path))
            bar.desc = "Loading LLM"
            bar.update()
            llm = LLM()
            bar.update()
        results = [llm.generate(results)
                   for results in tqdm(search_results.search_results,
                                       desc="Generating answers")]
        with tqdm(desc="Saving answers", total=1) as bar:
            makedirs(save_directory, exist_ok=True)
            dump_json(new_file_path(student_search_results_path,
                                    save_directory),
                      StudentSearchResultsAndAnswer(k=search_results.k,
                                                    search_results=results))
            bar.update()
        print()
        print(f"Answers saved at '{save_directory}'")

    def evaluate(self,
                 dataset_path: str = "data/datasets/AnsweredQuestions/"
                                     + "dataset_docs_public.json",
                 student_search_results_path: str = (
                     "data/output/search_results/dataset_docs_public.json")
                 ) -> None:
        """Evaluate search results against ground truth

        Parameters
        ----------
        dataset_path : str
            The ground truth dataset path
        student_search_results_path : str
            The search results file path to evaluate
        """

        print(f"Evaluating search results '{student_search_results_path}'",
              end="")
        print(f" against ground truth '{dataset_path}'")
        print()
        dataset = RagDataset.load(dataset_path, True)
        search_results = StudentSearchResults(**load_json(
            student_search_results_path))
        if len(dataset.rag_questions) != len(search_results.search_results):
            raise Exception("no matching comparaison data")
        if len(search_results.search_results) == 0:
            raise Exception("nothing to evaluate")
        recalls: Dict[int, List[float]] = {}
        for k in (1, 3, 5, 10):
            if k < search_results.k:
                recalls[k] = []
        recalls[search_results.k] = []
        for ground_truth, retrieved in tqdm(list(zip(
                dataset.rag_questions, search_results.search_results)),
                desc="Evaluating"):
            for k in recalls:
                recalls[k].append(Evaluator.recall_at_k(retrieved,
                                                        ground_truth,
                                                        k))
        print()
        print("Evaluation Results")
        print("========================================")
        print(f"Questions evaluated: {len(dataset.rag_questions)}")
        for k, v in recalls.items():
            print(f"Recall@{k}: {(sum(v) / len(v)):.3f}")
