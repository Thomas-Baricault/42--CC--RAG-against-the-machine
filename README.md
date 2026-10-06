*This project has been created as part of the curriculum by tbaricau*

# RAG against the machine

## Description

The goal of this project is to understand RAG (Retrieving Augmented Generation) and create a CLI that use this method.

The CLI must be able to index the entire content of a given repository and retrieve the sources for a given query in order to generate the best possible answer.

## Instructions

Install all the dependencies and create a virtual environment
```Shell
make install
```

Enter the virtual environment
```Shell
source .venv/bin/activate
```

Run default pipeline
```Shell
make run
```

Index the repository
```Shell
uv run python -m src index
```

Search for a single query
```Shell
uv run python -m src search <query>
```

Process multiple questions and output search results
```Shell
uv run python -m src search_dataset
```

Answer a single question with context
```Shell
uv run python -m src answer <query>
```

Generate answers from search results
```Shell
uv run python -m src answer_dataset
```

Evaluate search results against ground truth
```Shell
uv run python -m src evaluate
```

## Resources

What is RAG

<https://en.wikipedia.org/wiki/Retrieval-augmented_generation>

What is BM25

<https://en.wikipedia.org/wiki/Okapi_BM25>

Python ``fire`` usage

<https://google.github.io/python-fire/guide/>

Python ``tqdm`` usage

<https://tqdm.github.io>

Python ``bm25s`` usage

<https://bm25s.github.io>

I use AI to understand how to build my pipeline and to get example of code using ``bm25s`` and ``transformers``.

## System architecture

The RAG pipeline work as follow : Indexing -> Retrieving -> Augmenting -> Generating

We will also add an "Evaluating" section to calculate the relevence of our model.

### Indexing

First of all, we have to index the given repository. I created an Indexer class which take a repository path in parameter, index all this repository, and then save the result into 2 files (bm25_index and chunks).

To index the files, the indexer split them into chunks, and then create a corpus based on those chunks (simply by splitting the chunks into words). Finally, I use the ``bm25s`` library to create an index from those data.

### Retrieving

Once we have indexed the repository, we can search the most relievent sources for a given query. We just load the indexed data, and then for each query, I use ``bm25s`` to get the better k sources.

### Augmenting

Before the generation, I use the retrieved source to create a context and build a prompt for the LLM.

### Generating

I use the augmented prompt and give it to the LLM, and then I ask the LLM to generate a response.

### Evaluating

To evaluate the model, I compare the retrieved sources for a given query to the ground truth annotations.

I calculate how many retrieved sources match the ground truth and then divide by the number of ground truth sources to get an average score.

We consider that a source is found when at least 5% of the ground truth is overlaped by the retrieved source.

## Chunking strategy

All documents are chunked into chunk of 2000 characters maximum by default.

I add a special chunk strategy for Markdown (.md) and Python (.py) files.

For Markdown I split the document using titles, and for Python I split using classes of functions definitions. That improve the relevance of the created chunks.

## Retrieval method

I use BM25 with the ``bm25s`` library. To retrieve the most relevant sources I simply retrieve the sources for each query using the ``BM25`` object.

BM25 base it's score calculation on three concepts:
- TF (Term Frequency): the number of occurrences of a term in the source
- IDF (Inverse Document Frequency): less frequent words are weighted more heavily
- Document Length Normalisation: longer documents are not favored over shorter documents

## Performance analysis

For docs questions I got those recall@k:
- Recall@1: 0.570
- Recall@3: 0.790
- Recall@5: 0.830
- Recall@10: 0.890

This is far more than the 55% required.

And for code questions I got those recall@k:
- Recall@1: 0.380
- Recall@3: 0.510
- Recall@5: 0.560
- Recall@10: 0.630

This is also better than the expected 45%.

We observe that the larger k is, the more likely the source is to be found, which makes sense since the program has a greater chance of finding the source.

Le système est plus efficace pour les questions de documentation car BM25 est plus performant sur les textes contenant des mots et non sur les extraits de code.

## Design decisions

I divided the different stages of the RAG process into a separate class for each.

That give a better comprehensive code and structure.

The LLM class represent both augmenting and generating sections because those processus are linked (augmenting is simply building a prompt from the retrieved source).

## Challenges faced

During this project I faced multiple challenges.

First of all, how to chunk the files. I resolved this problem by using some regex that extremely simplify the code.

An other difficulty was to understand how to evaluate the RAG model. But I finally found how to do that.

## Example usage

First of all index the repository using:
```Shell
uv run python -m src index
```

And then you can ask whatever you want, for example:
```Shell
uv run python -m src answer "How work RAG?"
```
