PY			= python
VENV		= .venv

CLEARLINE	= \r\033[K
RESET		= \e[0m
BOLD		= \e[1m
RED			= \e[31m
GREEN		= \e[32m
YELLOW		= \e[33m
CYAN		= \e[36m
WHITE		= \e[37m
GREY		= \e[90m

define head
$(BOLD)$(GREY)[$(2)$(1)$(GREY)]$(RESET)
endef

HEAD_INFO		= $(call head,INFO,$(CYAN))
HEAD_SUCCESS	= $(call head,SUCCESS,$(GREEN))
HEAD_ERROR		= $(call head,ERROR,$(RED))

define step
	@printf "$(HEAD_INFO) $(1)..."; \
	out="$$( { $(2); } 2>&1 )"; \
	status="$$?"; \
	if [ "$$status" -eq 0 ]; then \
		printf "$(CLEARLINE)$(HEAD_SUCCESS) $(1)\n"; \
	else \
		printf "$(CLEARLINE)$(HEAD_ERROR) $(1)\n"; \
		printf "\n$$out\n\n"; \
		exit $$status; \
	fi
endef

define exec
	@printf "$(HEAD_INFO) $(1)...\n"; \
	$(2); \
	status="$$?"; \
	if [ "$$status" -eq 0 ]; then \
		printf "$(HEAD_SUCCESS) $(1)\n\n"; \
	else \
		printf "$(HEAD_ERROR) $(1)\n\n"; \
		exit $$status; \
	fi
endef

define log
	@printf "$(1) $(2)\n";
endef

all: install run

install:
	$(call exec,Installing requirements,uv sync --extra dev --cache-dir /tmp/.cache/uv)
	$(call log,$(HEAD_INFO),Run $(YELLOW)source $(VENV)/bin/activate$(RESET) to enter the environment and $(YELLOW)source ~/.zshrc$(RESET) to leave it)

run:
	$(call exec,Indexing repository,uv run $(PY) -m src index)
	$(call exec,Processing multiple questions,uv run $(PY) -m src search_dataset)
	$(call exec,Evaluating,uv run $(PY) -m src evaluate)

debug:
	$(call exec,Running main script in debug mode,uv run $(PY) -m pdb src index)

clean:
	$(call step,Removing __pycache__,rm -dfr $(shell find . -name '__pycache__'))
	$(call step,Removing .mypy_cache,rm -dfr $(shell find . -name '.mypy_cache'))
	$(call step,Removing .pytest_cache,rm -dfr $(shell find . -name '.pytest_cache'))
	$(call step,Removing .egg-info, rm -dfr $(shell find . -name '*.egg-info'))

lint:
	$(call step,Checking Norm,$(PY) -m flake8 .)
	$(call step,Checking Typing,$(PY) -m mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs)

lint-strict:
	$(call step,Checking Norm,$(PY) -m flake8 .)
	$(call step,Checking Typing,$(PY) -m mypy . --strict)

test:
	$(call exec,Running tests,uv run $(PY) -m pytest)

.PHONY: all install run debug clean lint lint-strict test
