from embedchain.config.BaseConfig import BaseConfig
from string import Template
import re

DEFAULT_PROMPT = """
  Use the following pieces of context to answer the query at the end.
  If you don't know the answer, just say that you don't know, don't try to make up an answer.

  $context

  Query: $query

  Helpful Answer:
"""

DEFAULT_PROMPT_WITH_HISTORY = """
  Use the following pieces of context to answer the query at the end.
  If you don't know the answer, just say that you don't know, don't try to make up an answer.
  I will provide you with our conversation history. 

  $context

  History: $history

  Query: $query

  Helpful Answer:
"""

DEFAULT_PROMPT_TEMPLATE = Template(DEFAULT_PROMPT)
DEFAULT_PROMPT_WITH_HISTORY_TEMPLATE = Template(DEFAULT_PROMPT_WITH_HISTORY)
query_re = re.compile(r"\$\{*query\}*")
context_re = re.compile(r"\$\{*context\}*")
history_re = re.compile(r"\$\{*context\}*")


class QueryConfig(BaseConfig):
    """
    Config for the `query` method.
    """
    def __init__(self, template: Template = None, history = None):
        """
        Initializes the QueryConfig instance.

        :param template: Optional. The `Template` instance to use as a template for prompt.
        :param history: Optional. A list of strings to consider as history.
        :raises ValueError: If the template is not valid as template should contain $context and $query
        """
        if not history:
            self.history = None
        else:
            if len(history) == 0:
                self.history = None
            else:
                self.history = history

        if template is None:
            if self.history is None:
                template = DEFAULT_PROMPT_TEMPLATE
            else:
                template = DEFAULT_PROMPT_WITH_HISTORY_TEMPLATE

        # Validate template without and with history
        if self.history is None:
            if not (re.search(query_re, template.template) \
                and re.search(context_re, template.template)):
                raise ValueError("`template` should have `query` and `context` keys")
        else:
            if not (re.search(query_re, template.template) \
                and re.search(context_re, template.template)
                and re.search(history_re, template.template)):
                raise ValueError("`template` should have `query`, `context` and `history` keys")

        self.template = template
