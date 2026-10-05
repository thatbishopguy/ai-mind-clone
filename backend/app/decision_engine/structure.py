"""Conservative, deterministic context extraction. No AI or recommendations."""
import re
from uuid import NAMESPACE_URL, uuid5

from app.models.analysis import Analysis, Context, Option
from app.models.decision import Decision

LABELS = {
    "actor": "actors", "actors": "actors", "people": "actors",
    "constraint": "constraints", "constraints": "constraints",
    "fact": "known_facts", "facts": "known_facts", "known fact": "known_facts",
    "unknown": "unknowns", "unknowns": "unknowns", "question": "unknowns",
    "problem": "problem", "decision": "problem", "option": "options",
}


def structure_decision(decision: Decision) -> Analysis:
    groups: dict[str, list[str]] = {
        name: [] for name in ["actors", "constraints", "known_facts", "unknowns", "problem", "options"]
    }
    unclassified = []
    for line in decision.situation.splitlines():
        line = line.strip()
        if not line:
            continue
        match = re.match(r"^(?:[-*] )?([A-Za-z ]+):\s*(.+)$", line)
        key = LABELS.get(match[1].strip().lower()) if match else None
        if key and match:
            groups[key].append(match[2].strip())
        else:
            unclassified.append(line)

    # Preserve free prose verbatim as the problem when no explicit problem was given.
    # Guessing actors, facts or options from ambiguous prose would invent certainty.
    problem = "\n".join(groups["problem"]) or decision.situation
    warnings = [
        "Rule-based draft: only explicitly labeled details are extracted. Review before use.",
        "Reported facts are user statements, not independently verified facts.",
    ]
    if unclassified:
        warnings.append("Unclassified text is preserved in the original situation; review it for missing context.")
    if not groups["options"]:
        warnings.append("No explicitly labeled options found. Add the choices you are considering.")
    context = Context(
        **decision.model_dump(include={"situation", "domain", "stakes", "time_pressure"}),
        problem=problem,
        actors=groups["actors"], constraints=groups["constraints"],
        known_facts=groups["known_facts"], unknowns=groups["unknowns"],
    )
    return Analysis(
        decision_id=decision.id, context=context, warnings=warnings,
        options=[Option(id=uuid5(NAMESPACE_URL, f"{decision.id}:option:{index}:{description}"),
                        description=description)
                 for index, description in enumerate(groups["options"])],
    )
