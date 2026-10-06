from __future__ import annotations
from bm25s import BM25, tokenize
from json import dump
from os import makedirs, walk
from os.path import join
from re import DOTALL, findall, finditer, MULTILINE
from typing import Generator, List
from .models import MinimalSource
from .utils import CHUNK_REGEX, MARKDOWN_REGEX, PYTHON_REGEX


class Indexer:
    """Class to index raw files repository

    Methods
    -------
    index(repo) -> None
        Index a repository
    save(folder) -> None
        Save the indexed data
    """

    class Document:
        """Representation of a document

        Attributes
        ----------
        path : str
            The path of the document
        content : str
            The document content

        Methods
        -------
        is_valid() -> bool
            Returns if the document is valid

        Class Methods
        -------------
        read_repo(repo) -> Generator[Indexer.Document, None, None]
            Retrieve all the documents in a repository
        """

        @classmethod
        def read_repo(cls,
                      repo: str) -> Generator[Indexer.Document, None, None]:
            """Retrieve all the documents in a repository

            Parameters
            ----------
            repo : str
                The repository path

            Yield
            -----
            Indexer.Document
                The documents
            """

            for root, _, files in walk(repo):
                for file in files:
                    document = cls(join(root, file))
                    if document.is_valid():
                        yield document

        def __init__(self, path: str) -> None:
            """
            Parameters
            ----------
            path : str
                The document path
            """

            self._path = path
            self._content: str | None = None
            try:
                with open(path, "r", encoding="utf8") as file:
                    self._content = file.read()
                    if self._content == "":
                        self._content = None
            except Exception:
                ...

        @property
        def path(self) -> str:
            """The path of the document

            Returns
            -------
            str
                The path
            """

            return self._path

        @property
        def content(self) -> str:
            """The document content

            Returns
            -------
            str
                The content
            """

            if self._content is None:
                raise Exception("not a valid document")
            return self._content

        def is_valid(self) -> bool:
            """Returns if the document is valid

            Returns
            -------
            bool
                True if the document is valid, False otherwise
            """

            return self._content is not None

    def __init__(self, max_chunk_size: int) -> None:
        """
        Parameters
        ----------
        max_chunk_size : int
            The maximum size of a source chunk of data

        Raises
        ------
        Exception
            If max_chunk_size is less than 1
        """

        if max_chunk_size < 1:
            raise Exception("max_chunk_size must be greater or equal to 1")
        self._max_chunk_size = max_chunk_size
        self._bm25: BM25 | None = None
        self._chunks: List[MinimalSource] = []

    def index(self, repo: str) -> None:
        """Index a repository

        Parameters
        ----------
        repo : str
            The repository path
        """

        self._bm25 = None
        self._chunks.clear()
        corpus = []
        for document in Indexer.Document.read_repo(repo):
            for source in Indexer._chunk_document(document,
                                                  self._max_chunk_size):
                self._chunks.append(source)
                corpus.append(document.content[source.first_character_index:
                                               source.last_character_index])
        if len(self._chunks) == 0:
            raise Exception("no valid chunk found")
        self._bm25 = BM25(corpus=corpus)
        self._bm25.index(tokenize(corpus))

    def save(self, folder: str) -> None:
        """Save the indexed data

        Parameters
        ----------
        folder : str
            The folder in which save the data
        """

        if self._bm25 is None:
            raise Exception("cannot save before indexing")
        chunks_path = join(folder, "chunks")
        makedirs(folder, exist_ok=True)
        makedirs(chunks_path, exist_ok=True)
        self._bm25.save(join(folder, "bm25_index"))
        with open(join(chunks_path, "chunks.json"), "w") as file:
            dump([chunk.model_dump() for chunk in self._chunks], file)

    @staticmethod
    def _chunk_simple(document: Indexer.Document, source: MinimalSource,
                      max_chunk_size: int
                      ) -> Generator[MinimalSource, None, None]:
        start = source.first_character_index
        content = document.content[source.first_character_index:
                                   source.last_character_index]
        for block in findall(CHUNK_REGEX.format(max_chunk_size,
                                                max_chunk_size),
                             content, DOTALL):
            yield MinimalSource(file_path=document.path,
                                first_character_index=start,
                                last_character_index=start + len(block) - 1)
            start += len(block)

    @staticmethod
    def _chunk_default(document: Indexer.Document
                       ) -> Generator[MinimalSource, None, None]:
        yield MinimalSource(file_path=document.path,
                            first_character_index=0,
                            last_character_index=len(document.content) - 1)

    @staticmethod
    def _chunk_regex(document: Indexer.Document, pattern: str,
                     ) -> Generator[MinimalSource, None, None]:
        matches = list(finditer(pattern, document.content, MULTILINE))
        if len(matches) == 0:
            for chunk in Indexer._chunk_default(document):
                yield chunk
        for i, m in enumerate(matches):
            start = m.start()
            if i == 0 and start > 0:
                yield MinimalSource(file_path=document.path,
                                    first_character_index=0,
                                    last_character_index=start - 1)
            if i + 1 == len(matches):
                end = len(document.content)
            else:
                end = matches[i + 1].start() - 1
            if start < end:
                yield MinimalSource(file_path=document.path,
                                    first_character_index=start,
                                    last_character_index=end - 1)

    @staticmethod
    def _chunk_document(document: Indexer.Document, max_chunk_size: int
                        ) -> Generator[MinimalSource, None, None]:
        if document.path.endswith(".py"):
            gen = Indexer._chunk_regex(document, PYTHON_REGEX)
        elif document.path.endswith(".md"):
            gen = Indexer._chunk_regex(document, MARKDOWN_REGEX)
        else:
            gen = Indexer._chunk_default(document)
        for chunk in gen:
            for c in Indexer._chunk_simple(document, chunk, max_chunk_size):
                yield c
