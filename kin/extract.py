"""Photo → document type and transcribed fields, with the Token Factory vision model.

The model only transcribes. Everything after this (uncertainty checks, conflicts, records,
reminders) is deterministic code in `kin.intake`, and nothing becomes active until the Admin
confirms it.
"""

from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

MED = "array of {drug, strength, directions%s}, one per table row"
SCHEMAS: dict[str, dict[str, str]] = {
    # Fields tied to a printed heading are filled only when that heading is on this page:
    # a page without it must give [] (each page of a summary is sent as its own photo).
    "discharge_summary": {
        "hospital": "string",
        "admission_date": "string, from the 'Admitted' cell",
        "discharge_date": "string, from the 'Discharged' cell",
        "diagnoses": "array of strings under the heading 'Diagnoses', without list numbers",
        "medications_before": (MED % "") + " under the heading 'Medications before admission'",
        "medications_after": (MED % ", change") + " under the heading 'Discharge medications'",
        "follow_up": "array of the bullet items under the heading 'Follow-up'",
    },
    "medication_label": {
        k: "string"
        for k in ("drug", "strength", "directions", "quantity", "dispensed_date", "pharmacy")
    },
    "appointment_slip": {
        "clinic": "string",
        "department": "string",
        "doctor": "string",
        "date": "string",
        "time": "string",
        "instructions": "array of strings",
    },
    "clinic_memo": {
        "clinic": "string",
        "date": "string",
        "clinician": "string",
        "notes": "array of strings",
        "medication_changes": "array of {drug, change, dose}",
    },
    "insurance_letter": {k: "string" for k in ("insurer", "date", "claim_ref", "status", "amount")},
    "carer_note": {"date": "string", "observations": "array of strings, one per line item"},
}
# Fields printed under a section heading are extracted only when the page shows that heading:
# asked to fill a section that is on the other page, the model copies a table it can see.
# Detecting headings first is reliable (12/12 on the fixture photos and renders).
SECTION_GATES: dict[str, dict[str, str]] = {
    "discharge_summary": {
        "admission_date": "Diagnoses",
        "discharge_date": "Diagnoses",
        "diagnoses": "Diagnoses",
        "medications_after": "Discharge medications",
        "medications_before": "Medications before admission",
        "follow_up": "Follow-up",
    }
}
DESCRIPTIONS = {
    "discharge_summary": "a hospital discharge summary (any page)",
    "medication_label": "a pharmacy label for one medicine",
    "appointment_slip": "an appointment slip or card",
    "clinic_memo": "a memo or letter from a clinic or doctor",
    "insurance_letter": "a letter from an insurer about a claim",
    "carer_note": "a handwritten note",
}


class Client(Protocol):
    chat: Any


@dataclass
class Extraction:
    doc_type: str
    fields: dict[str, Any] = field(default_factory=dict)
    uncertain: list[str] = field(default_factory=list)


def _ask(client: Client, model: str, image: bytes, mime: str, prompt: str, max_tokens: int) -> str:
    url = f"data:{mime};base64,{base64.b64encode(image).decode()}"
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        max_tokens=max_tokens,
        # MiniCPM-V 4.5 "thinks" by default; transcription needs no reasoning, only the answer.
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": url}},
                ],
            }
        ],
    )
    text = resp.choices[0].message.content or ""
    return re.sub(r"(?s)<think>.*?(</think>|$)", "", text).strip()


def parse_json(text: str) -> dict[str, Any]:
    """The first JSON object in a reply (models sometimes wrap it in a code fence)."""
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in the reply")
    return json.loads(text[start : end + 1])


def classify(client: Client, model: str, image: bytes, mime: str) -> str:
    options = "; ".join(f"{k} ({v})" for k, v in DESCRIPTIONS.items())
    reply = _ask(
        client,
        model,
        image,
        mime,
        f"What kind of document is in this photo? Options: {options}; other. "
        "Reply with only the option name.",
        20,
    ).lower()
    return next((k for k in SCHEMAS if k in reply), "other")


def headings_on_page(
    client: Client, model: str, image: bytes, mime: str, headings: list[str]
) -> set[str]:
    reply = _ask(
        client,
        model,
        image,
        mime,
        "Which of these section headings are printed on this page? Headings: "
        + "; ".join(headings)
        + ". Reply with only the headings that appear, separated by semicolons, or 'none'.",
        60,
    ).lower()
    return {h for h in headings if h.lower() in reply}


def extract(client: Client, model: str, image: bytes, mime: str, doc_type: str) -> Extraction:
    schema = dict(SCHEMAS[doc_type])
    gates = SECTION_GATES.get(doc_type, {})
    if gates:
        present = headings_on_page(client, model, image, mime, sorted(set(gates.values())))
        schema = {k: v for k, v in schema.items() if k not in gates or gates[k] in present}
    keys = "; ".join(f"{k} ({v})" for k, v in schema.items())
    prompt = (
        "Transcribe these fields from the photographed document exactly as printed: keep the "
        "original wording, capitalisation, units and date format; do not add or normalise "
        "anything. Use null or [] for a field whose heading or label is not on this page; never "
        "copy rows from another section to fill one. Also give 'uncertain': the list of keys you "
        "could not read clearly. Reply with only a JSON object with keys: "
        f"{keys}; uncertain."
    )
    data = parse_json(_ask(client, model, image, mime, prompt, 1500))
    fields = {k: data.get(k) for k in schema if data.get(k) not in (None, "", [])}
    uncertain = [str(u) for u in data.get("uncertain") or [] if str(u) in schema]
    if doc_type == "discharge_summary":
        fields["diagnoses"] = [re.sub(r"^\d+[.)]\s*", "", d) for d in fields.get("diagnoses", [])]
        if not fields["diagnoses"]:
            fields.pop("diagnoses")
    return Extraction(doc_type=doc_type, fields=fields, uncertain=uncertain)
