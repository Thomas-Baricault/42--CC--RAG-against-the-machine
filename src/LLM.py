from torch import cuda, float16, float32, no_grad
from torch.backends import mps
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
from .models import MinimalAnswer, MinimalSearchResults


class LLM:
    """Representation of an LLM

    Methods
    -------
    generate(search_results) -> MinimalAnswer
        Generate an answer based on search results
    """

    def __init__(self) -> None:
        self._name = "Qwen/Qwen3-0.6B"
        if mps.is_available():
            # self._device = "mps"
            self._dtype = float16
        elif cuda.is_available():
            # self._device = "cuda"
            self._dtype = float16
        else:
            # self._device = "cpu"
            self._dtype = float32
        self._tokenizer = AutoTokenizer.from_pretrained(self._name)
        if self._tokenizer.pad_token_id is None:
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id
        config = AutoConfig.from_pretrained(self._name)
        config.tie_word_embeddings = False
        self._model = AutoModelForCausalLM.from_pretrained(
            self._name,
            config=config,
            dtype=self._dtype
        )
        self._model.config.tie_word_embeddings = False
        self._model.generation_config.temperature = None
        self._model.generation_config.top_p = None
        self._model.generation_config.top_k = None
        # self._model.to(self._device).eval()
        for p in self._model.parameters():
            p.requires_grad = False

    def generate(self,
                 search_results: MinimalSearchResults) -> MinimalAnswer:
        """Generate an answer based on search results

        Parameters
        ----------
        search_results : MinimalSearchResults
            The search results

        Returns
        -------
        MinimalAnswer
            The generated answer
        """

        context = ""
        for source in search_results.retrieved_sources:
            with open(source.file_path, "r", encoding="utf8") as file:
                content = file.read()[source.first_character_index:
                                      source.last_character_index + 1]
                context += f"\nFile: {source.file_path}\n{content[:200]}\n"
        prompt = ("You are an expert assistant.\n" +
                  "Use ONLY the provided context to answer.\n" +
                  "\n" +
                  "Context:\n" +
                  f"{context[:5000]}\n" +
                  "\n" +
                  "Question:\n" +
                  f"{search_results.question}\n" +
                  "\n" +
                  "Answer:\n")
        inputs = self._tokenizer(prompt,
                                 return_tensors="pt",
                                 truncation=True,
                                 max_length=2048)
        # .to(self._device)
        with no_grad():
            outputs = self._model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                do_sample=False,
                # repetition_penalty=1.1
            )
        decoded = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        if isinstance(decoded, list):
            decoded = "".join(decoded)
        return MinimalAnswer(**search_results.model_dump(),
                             answer=decoded[len(prompt):])
