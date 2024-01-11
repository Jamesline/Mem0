import concurrent.futures
import logging
import os
from string import Template
from typing import Optional

import numpy as np
from openai import OpenAI
from tqdm import tqdm

from embedchain.config.eval.base import GroundednessConfig
from embedchain.eval.base import BaseMetric
from embedchain.utils.eval import EvalData


class Groundedness(BaseMetric):
    """
    Metric for groundedness (aka faithfulness) of answer from the given contexts.
    """

    def __init__(self, config: Optional[GroundednessConfig] = None):
        self.config = config or GroundednessConfig()
        api_key = self.config.api_key or os.environ["OPENAI_API_KEY"]
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable or pass the `api_key` in config.")
        self.client = OpenAI(api_key=api_key)

    def _generate_answer_claim_prompt(self, data: EvalData) -> str:
        """
        Generate the prompt for the given data.
        """
        prompt = Template(self.config.answer_claims_prompt).substitute(question=data.question, answer=data.answer)
        return prompt

    def _get_claim_statements(self, prompt: str) -> list[str]:
        """
        Get claim statements from the answer.
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": f"{prompt}"}],
        )
        result = response.choices[0].message.content.strip()
        claim_statements = [statement for statement in result.split("\n") if statement]
        return claim_statements

    def _generate_claim_inference_prompt(self, data: EvalData, claim_statements: list[str]) -> str:
        """
        Generate the claim inference prompt for the given data and claim statements.
        """
        prompt = Template(self.config.claims_inference_prompt).substitute(
            context="\n".join(data.contexts), claim_statements="\n".join(claim_statements)
        )
        return prompt

    def _get_claim_verdict_scores(self, prompt: str) -> list[int]:
        """
        Get verdicts for claim statements.
        """
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=[{"role": "user", "content": f"{prompt}"}],
        )
        result = response.choices[0].message.content.strip()
        claim_verdicts = result.split("\n")
        verdict_score_map = {"1": 1, "0": 0, "-1": np.nan}
        verdict_scores = []
        for verdict in claim_verdicts:
            verdict_scores.append(verdict_score_map[verdict])
        return verdict_scores

    def _compute_score(self, data: EvalData) -> float:
        """
        Compute the groundedness score (aka faithfulness) for a single data point.
        """
        answer_claims_prompt = self._generate_answer_claim_prompt(data)
        claim_statements = self._get_claim_statements(answer_claims_prompt)

        claim_inference_prompt = self._generate_claim_inference_prompt(data, claim_statements)
        verdict_scores = self._get_claim_verdict_scores(claim_inference_prompt)
        return sum(verdict_scores) / len(claim_statements)

    def evaluate(self, dataset: list[EvalData]):
        """
        Evaluate the dataset and returns the average groundedness score.
        """
        results = []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_data = {executor.submit(self._compute_score, data): data for data in dataset}
            for future in tqdm(
                concurrent.futures.as_completed(future_to_data),
                total=len(future_to_data),
                desc="Evaluating groundedness (aka faithfulness)",
            ):
                data = future_to_data[future]
                try:
                    score = future.result()
                    results.append(score)
                except Exception as e:
                    logging.error(f"Error while evaluating groundedness for data point {data}: {e}")

        return np.mean(results) if results else 0.0
