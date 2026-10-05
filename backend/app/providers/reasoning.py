import json
from typing import Protocol

from openai import APIError, APITimeoutError, OpenAI, RateLimitError
from pydantic import ValidationError

from app.models.analysis import Analysis
from app.models.decision import Decision
from app.models.suggestion import ProposedContext
from app.providers.prompts import SYSTEM_PROMPT


class ProviderFailure(Exception):
    """Safe user-facing failure category; never forward provider error bodies."""


class ReasoningProvider(Protocol):
    def suggest(self, decision: Decision, analysis: Analysis) -> ProposedContext: ...


class OpenAIReasoning:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def suggest(self, decision: Decision, analysis: Analysis) -> ProposedContext:
        payload = json.dumps({"decision": decision.model_dump(mode="json"),
                              "context": analysis.context.model_dump(mode="json"),
                              "options": [o.description for o in analysis.options]})
        try:
            with OpenAI(api_key=self.api_key, timeout=30.0, max_retries=0) as client:
                response = client.responses.parse(
                    model=self.model,
                    input=[{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": payload}],
                    text_format=ProposedContext, max_output_tokens=2500, store=False,
                )
            if any(getattr(part, "type", None) == "refusal"
                   for item in response.output for part in getattr(item, "content", [])):
                raise ProviderFailure("AI declined to provide suggestions.")
            if response.status != "completed":
                raise ProviderFailure("AI returned an incomplete response.")
            if response.output_parsed is None:
                raise ProviderFailure("AI did not return valid structured suggestions.")
            proposal = ProposedContext.model_validate(response.output_parsed)
        except APITimeoutError as exc:
            raise ProviderFailure("AI request timed out.") from exc
        except RateLimitError as exc:
            raise ProviderFailure("AI usage limit reached or service is busy.") from exc
        except (APIError, ValidationError, ValueError) as exc:
            raise ProviderFailure("AI service is unavailable or returned invalid data.") from exc
        # A schema-valid response can still invent facts. Reject unsupported quotes.
        sources = [decision.situation, analysis.context.problem, *analysis.context.actors,
                   *analysis.context.constraints, *analysis.context.known_facts,
                   *analysis.context.unknowns]
        if not proposal.problem.strip() or any(not o.description.strip() for o in proposal.options):
            raise ProviderFailure("AI returned empty required details.")
        if any(not fact.source_quote.strip() or not fact.statement.strip() or
               not any(fact.source_quote in source for source in sources)
               for fact in proposal.reported_facts):
            raise ProviderFailure("AI returned facts without matching source quotes.")
        return proposal
