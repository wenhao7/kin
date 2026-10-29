"""Intake: extraction → draft → Admin checks → active records and reminders (docs/04, docs/05).

Everything here is deterministic. The model's transcription becomes a *draft*; issues are found
by code (a drug name that matches no known record, a date with two different times, a field the
model could not read) and put to the Admin one at a time. Only a confirmed draft creates active
records and events. Reminder times come from the document's own words mapped to the household's
routine (config/members.yaml) and are shown in the draft for the Admin to confirm; Kin never
infers a dose or a time.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

from kin.store import Store, new_id

TITLES = {
    "discharge_summary": "Discharge summary",
    "medication_label": "Medication label",
    "appointment_slip": "Appointment slip",
    "clinic_memo": "Clinic memo",
    "insurance_letter": "Insurance letter",
    "carer_note": "Carer note",
}
DATE_RE = re.compile(
    r"\b(\d{1,2}) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* (\d{4})\b"
)
TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2}) ?([ap]m)\b", re.IGNORECASE)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
CONFIRM, DISCARD = "Confirm", "Discard"


# --- small parsers --------------------------------------------------------------------------
def parse_date(text: str) -> date | None:
    m = DATE_RE.search(text or "")
    if not m:
        return None
    return date(int(m.group(3)), MONTHS.index(m.group(2)) + 1, int(m.group(1)))


def parse_time(text: str) -> str | None:
    m = TIME_RE.search(text or "")
    if not m:
        return None
    hour, minute, ampm = int(m.group(1)), int(m.group(2)), m.group(3).lower()
    hour = hour % 12 + (12 if ampm == "pm" else 0)
    return f"{hour:02d}:{minute:02d}"


def show_date(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def doc_date(doc_type: str, fields: dict[str, Any]) -> str:
    """The document's own date; an appointment slip's date is the appointment's, not the slip's."""
    if doc_type == "appointment_slip":
        return ""
    for key in ("discharge_date", "dispensed_date", "date", "admission_date"):
        if fields.get(key):
            d = parse_date(str(fields[key]))
            if d:
                return show_date(d)
    return ""


def source_of(doc_type: str, fields: dict[str, Any]) -> str:
    when = doc_date(doc_type, fields)
    return (
        f"{TITLES.get(doc_type, 'Document')}, {when}" if when else TITLES.get(doc_type, "Document")
    )


# --- reminder times from the document's words --------------------------------------------------
def proposed_times(directions: str, times: dict[str, Any]) -> list[str]:
    """Household times for a direction's own words; [] when the words name no time."""
    d = (directions or "").lower()
    if not d or "do not take" in d:
        return []
    if "three times" in d:
        return list(times.get("three_times_after_food", []))
    if "twice" in d and "breakfast" in d and "dinner" in d:
        return [times["breakfast"], times["dinner"]]
    if "before breakfast" in d:
        return [times["before_breakfast"]]
    if "morning" in d:
        return [times["morning"]]
    if "night" in d or "bedtime" in d:
        return [times["night"]]
    return []


def med_label(f: dict[str, Any]) -> str:
    """“Drug strength: directions”, without empty parts."""
    name = " ".join(x for x in (f.get("drug", ""), f.get("strength", "")) if x)
    return f"{name}: {f.get('directions', '')}" if f.get("directions") else name


def per_day(directions: str) -> int | None:
    d = (directions or "").lower()
    for words, n in (("three times", 3), ("twice", 2), ("once", 1)):
        if words in d:
            return n
    return None


def until_of(directions: str) -> str | None:
    m = re.search(r"until (.+)$", directions or "", re.IGNORECASE)
    d = parse_date(m.group(1)) if m else None
    return d.isoformat() if d else None


# --- extraction → records ----------------------------------------------------------------------
def records_for(
    doc_type: str,
    fields: dict[str, Any],
    household: dict[str, Any],
    active_drugs: set[str] = frozenset(),
    extra: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Records a confirmed document produces (also used to seed the fixture). `excerpts` are the
    names of approved excerpts to attach when the caller has them (the fixture does); `quote`
    names the record's fields that are printed text, which a confirmed intake files as excerpts."""
    src = source_of(doc_type, fields)
    times = household.get("times", {})
    meds_by = household.get("medicines_by")
    extra = extra or {}
    out: list[dict[str, Any]] = []
    if doc_type == "discharge_summary":
        medical: dict[str, Any] = {}
        if fields.get("admission_date") and fields.get("discharge_date"):
            medical["summary"] = (
                f"Hospital stay {fields['admission_date']} to {fields['discharge_date']}; "
                "medication changes on discharge."
            )
        if fields.get("diagnoses"):
            medical["diagnoses"] = fields["diagnoses"]
        if fields.get("follow_up"):
            medical["follow_up"] = fields["follow_up"]
            care = [f for f in fields["follow_up"] if "emergency" in f.lower()]
            if care:
                medical["care_instructions"] = care
        if medical:
            out.append(
                {
                    "category": "medical",
                    "fields": {**medical, "source": src},
                    "excerpts": ["return-advice"],
                    "quote": ["care_instructions"],
                }
            )
        # A dated follow-up is an appointment: the family may read it, and it gets a reminder.
        for item in fields.get("follow_up") or []:
            when, m = _date_times(item), DATE_RE.search(item)
            if not when or m is None or "emergency" in item.lower():
                continue
            out.append(
                {
                    "category": "appointments",
                    "kind": "appointment",
                    "fields": {
                        "department": item[: m.start()].strip(" :,-"),
                        "date": show_date(when[0][0]),
                        "time": _ampm(when[0][1]),
                        "follow_up": item,
                        "source": src,
                    },
                    "assignee": household.get("appointments_by"),
                    "from_follow_up": True,
                    "excerpts": [],
                    "quote": ["follow_up"],
                }
            )
        for m in fields.get("medications_after") or []:
            out.append(
                {
                    "category": "medication",
                    "kind": "schedule",
                    "fields": {
                        "drug": m.get("drug", ""),
                        "strength": m.get("strength", ""),
                        "directions": m.get("directions", ""),
                        "change": m.get("change", ""),
                        "times": proposed_times(m.get("directions", ""), times),
                        "source": src,
                    },
                    "assignee": meds_by,
                    "excerpts": ["medication-changes"],
                    "quote": ["drug", "strength", "directions", "change"],
                }
            )
    elif doc_type == "medication_label":
        out.append(
            {
                "category": "medication",
                "kind": "dispensing",
                "fields": {
                    "drug": fields.get("drug", ""),
                    "strength": fields.get("strength", ""),
                    "directions": fields.get("directions", ""),
                    "quantity": fields.get("quantity", ""),
                    "dispensed": fields.get("dispensed_date", ""),
                    "pharmacy": fields.get("pharmacy", ""),
                    "source": src,
                },
                "excerpts": [],
                "quote": ["drug", "strength", "directions"],
            }
        )
        if str(fields.get("drug", "")).lower() not in active_drugs:
            out.append(
                {
                    "category": "medication",
                    "kind": "schedule",
                    "fields": {
                        "drug": fields.get("drug", ""),
                        "strength": fields.get("strength", ""),
                        "directions": fields.get("directions", ""),
                        "times": proposed_times(fields.get("directions", ""), times),
                        "source": src,
                    },
                    "assignee": meds_by,
                    "excerpts": [],
                }
            )
    elif doc_type == "appointment_slip":
        out.append(
            {
                "category": "appointments",
                "kind": "appointment",
                "fields": {
                    **{
                        k: fields[k]
                        for k in ("clinic", "department", "date", "time", "instructions")
                        if k in fields
                    },
                    "doctor": fields.get("doctor") or extra.get("doctor", ""),
                    "source": src,
                },
                "assignee": household.get("appointments_by"),
                "excerpts": [],
                "quote": ["instructions"],
            }
        )
    elif doc_type == "clinic_memo":
        memo_date, clinician = fields.get("date", ""), fields.get("clinician", "")
        out.append(
            {
                "category": "medical",
                "fields": {
                    "summary": f"{fields.get('clinic', 'Clinic')} review"
                    + (f" with {clinician}" if clinician else "")
                    + f", {memo_date}.",
                    "notes": fields.get("notes", []),
                    # Also here, not only in the schedule below: a later document's "Unchanged"
                    # replaces that schedule, but what was decided at the review stays true.
                    **(
                        {"medication_changes": fields["medication_changes"]}
                        if fields.get("medication_changes")
                        else {}
                    ),
                    "source": src,
                },
                "excerpts": ["plan"],
            }
        )
        for c in fields.get("medication_changes") or []:
            out.append(
                {
                    "category": "medication",
                    "kind": "schedule",
                    "fields": {
                        "drug": c.get("drug", ""),
                        "change": f"{c.get('change', '')} on {memo_date} ({clinician})",
                        "directions": c.get("dose", ""),
                        "times": proposed_times(c.get("dose", ""), times),
                        "source": src,
                    },
                    "assignee": meds_by,
                    "excerpts": ["plan"],
                    "quote": ["drug", "directions"],
                }
            )
    elif doc_type == "insurance_letter":
        out.append(
            {
                "category": "finance",
                "fields": {**fields, "source": src},
                "excerpts": ["status"],
                "quote": ["status"],
            }
        )
    elif doc_type == "carer_note":
        out.append(
            {
                "category": "observations",
                "fields": {
                    "date": fields.get("date", ""),
                    "observations": fields.get("observations", []),
                    "source": src,
                },
                "created_by": extra.get("author") or meds_by,
                "excerpts": [],
                "quote": ["observations"],
            }
        )
    else:
        raise ValueError(f"no mapping for {doc_type}")
    return out


# --- drafts and issues ------------------------------------------------------------------------
def known_drugs(store: Store) -> set[str]:
    with store._db() as db:
        rows = db.execute(
            "SELECT DISTINCT json_extract(fields,'$.drug') AS d FROM records"
            " WHERE category='medication'"
        ).fetchall()
    return {r["d"] for r in rows if r["d"]}


def _drug_slots(doc_type: str, fields: dict[str, Any]) -> list[tuple[str, str]]:
    if doc_type == "discharge_summary":
        return [
            (f"medications_after[{i}].drug", m.get("drug", ""))
            for i, m in enumerate(fields.get("medications_after") or [])
        ]
    if doc_type == "medication_label":
        return [("drug", fields.get("drug", ""))]
    if doc_type == "clinic_memo":
        return [
            (f"medication_changes[{i}].drug", c.get("drug", ""))
            for i, c in enumerate(fields.get("medication_changes") or [])
        ]
    return []


def get_path(fields: dict[str, Any], path: str) -> Any:
    cur: Any = fields
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        cur = cur[int(part[1:-1])] if part.startswith("[") else cur.get(part)
    return cur


def set_path(fields: dict[str, Any], path: str, value: Any) -> None:
    parts = re.findall(r"[^.\[\]]+|\[\d+\]", path)
    cur: Any = fields
    for part in parts[:-1]:
        cur = cur[int(part[1:-1])] if part.startswith("[") else cur[part]
    last = parts[-1]
    if last.startswith("["):
        cur[int(last[1:-1])] = value
    else:
        cur[last] = value


def find_issues(
    store: Store, doc_type: str, fields: dict[str, Any], uncertain: list[str]
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    known = known_drugs(store)
    lowered = {k.lower(): k for k in known}
    for path, name in _drug_slots(doc_type, fields):
        if not name or name.lower() in lowered:
            continue
        match = difflib.get_close_matches(name.lower(), list(lowered), n=1, cutoff=0.7)
        if match:
            suggestion = lowered[match[0]]
            issues.append(
                {
                    "id": f"name:{path}",
                    "kind": "name",
                    "path": path,
                    "question": f"I read the medicine as “{name}”, which matches no record. "
                    f"Did you mean {suggestion}?",
                    "options": [suggestion, f"Keep {name}"],
                    "values": {suggestion: suggestion, f"Keep {name}": name},
                    "resolved": False,
                }
            )
    for key in uncertain:
        if key in fields and not any(i["path"].startswith(key) for i in issues):
            value = fields[key]
            issues.append(
                {
                    "id": f"uncertain:{key}",
                    "kind": "uncertain",
                    "path": key,
                    "question": f"The {key.replace('_', ' ')} was hard to read: "
                    f"I have “{value}”. Is that right?",
                    "options": ["Correct", "I'll type it"],
                    "values": {"Correct": value},
                    "resolved": False,
                }
            )
    issues += _time_conflicts(store, doc_type, fields)
    return issues


def _date_times(text: str) -> list[tuple[date, str]]:
    out = []
    for m in DATE_RE.finditer(text):
        d = parse_date(m.group(0))
        t = parse_time(text[m.end() : m.end() + 14])
        if d and t:
            out.append((d, t))
    return out


def _time_conflicts(store: Store, doc_type: str, fields: dict[str, Any]) -> list[dict[str, Any]]:
    """Same date, different time, between this draft and an active record."""
    import json

    if doc_type == "appointment_slip":
        d, t = parse_date(str(fields.get("date", ""))), parse_time(str(fields.get("time", "")))
        mine = [(d, t, "time", str(fields.get("time")))] if d and t else []
    elif doc_type == "discharge_summary":
        mine = [
            (d, t, f"follow_up[{i}]", item)
            for i, item in enumerate(fields.get("follow_up") or [])
            for d, t in _date_times(item)
        ]
    else:
        return []
    issues = []
    for row in store.active_records(["appointments"]):  # a summary's dated follow-ups are here
        f = json.loads(row["fields"])
        d2, t2 = parse_date(str(f.get("date", ""))), parse_time(str(f.get("time", "")))
        theirs = [(d2, t2)] if d2 and t2 else []
        for d, t, path, _shown in mine:
            for d2, t2 in theirs:
                if d == d2 and t != t2:
                    src = json.loads(row["fields"]).get("source", "another document")
                    here, there = _ampm(t), _ampm(t2)
                    issues.append(
                        {
                            "id": f"conflict:{path}:{row['id']}",
                            "kind": "conflict",
                            "path": path,
                            "question": f"{show_date(d)}: this says {here}, "
                            f"the {src} says {there}. "
                            "Which time is right?",
                            "options": [
                                f"{here} (this document)",
                                f"{there} ({src.split(',')[0]})",
                            ],
                            "values": {
                                f"{here} (this document)": t,
                                f"{there} ({src.split(',')[0]})": t2,
                            },
                            "record": row["id"] if doc_type == "discharge_summary" else None,
                            "resolved": False,
                        }
                    )
    return issues


def _ampm(hhmm: str) -> str:
    h, m = map(int, hhmm.split(":"))
    return f"{(h % 12) or 12}:{m:02d} {'am' if h < 12 else 'pm'}"


def new_draft(
    store: Store,
    admin: str,
    document_id: str,
    doc_type: str,
    fields: dict[str, Any],
    uncertain: list[str],
) -> dict[str, Any]:
    """A new draft, or the open draft of the same document type merged (multi-page documents)."""
    for d in reversed(store.open_drafts(admin)):
        age = datetime.now(timezone.utc) - datetime.fromisoformat(d["created_at"])
        if d["doc_type"] == doc_type == "discharge_summary" and age < timedelta(minutes=20):
            merged = dict(d["fields"])
            for k, v in fields.items():
                if isinstance(v, list) and isinstance(merged.get(k), list):
                    merged[k] = merged[k] + [x for x in v if x not in merged[k]]
                elif k not in merged:
                    merged[k] = v
            d["fields"] = merged
            d["document_ids"] = d["document_ids"] + [document_id]
            d["issues"] = [i for i in d["issues"] if i["resolved"]] + [
                i
                for i in find_issues(store, doc_type, merged, uncertain)
                if i["id"] not in {r["id"] for r in d["issues"] if r["resolved"]}
            ]
            store.save_draft(d)
            return d
    draft = {
        "id": new_id("draft"),
        "admin": admin,
        "document_ids": [document_id],
        "doc_type": doc_type,
        "fields": fields,
        "issues": find_issues(store, doc_type, fields, uncertain),
        "status": "open",
    }
    store.save_draft(draft)
    return draft


def refresh_issues(store: Store, draft: dict[str, Any]) -> bool:
    """Re-check a draft against what is filed now (a document confirmed while this draft
    waited can clash with it); adds new questions, keeps answered ones. True if any were added."""
    known = {i["id"] for i in draft["issues"]}
    found = find_issues(store, draft["doc_type"], draft["fields"], [])
    new = [i for i in found if i["id"] not in known]
    draft["issues"] += new
    return bool(new)


def missing_sections(draft: dict[str, Any]) -> list[str]:
    """Headings of a multi-page document not seen on any page so far."""
    from kin.extract import SECTION_GATES

    gates = SECTION_GATES.get(draft["doc_type"], {})
    return sorted({h for k, h in gates.items() if not draft["fields"].get(k)})


def render_draft(draft: dict[str, Any], household: dict[str, Any], roster) -> str:
    f, t = draft["fields"], draft["doc_type"]
    lines = [f"Draft from the {source_of(t, f)} — please check before anything is filed:"]
    for r in records_for(t, f, household):
        rf = r["fields"]
        g = lambda k, rf=rf: rf.get(k, "")  # noqa: E731
        if r["category"] == "medication" and r.get("kind") == "schedule":
            times = ", ".join(rf.get("times") or []) or "no reminder"
            change = f" ({g('change')})" if g("change") else ""
            lines.append(f"• {g('drug')} {g('strength')}: {g('directions')}{change} → {times}")
        elif r.get("kind") == "dispensing":
            lines.append(
                f"• Dispensed {g('quantity')} of {g('drug')} {g('strength')} on {g('dispensed')}"
                f" ({g('pharmacy')})"
            )
        elif r["category"] == "appointments":
            lines.append(
                f"• Appointment: {g('department')}, {g('date')}, {g('time')} ({g('clinic')})"
            )
        elif r["category"] == "medical":
            for key in ("summary", "diagnoses", "follow_up"):
                if rf.get(key):
                    value = "; ".join(rf[key]) if isinstance(rf[key], list) else rf[key]
                    lines.append(f"• {key.replace('_', ' ').capitalize()}: {value}")
        elif r["category"] == "observations":
            lines.append(f"• Observations ({g('date')}): " + "; ".join(rf["observations"]))
        elif r["category"] == "finance":
            lines.append(f"• {g('insurer')} claim {g('claim_ref')}: {g('status')} ({g('amount')})")
    who = roster.by_id(household.get("medicines_by", "")) if household.get("medicines_by") else None
    if who and any(r.get("kind") == "schedule" for r in records_for(t, f, household)):
        lines.append(f"Medicine reminders go to {who.short} at the times shown.")
    missing = missing_sections(draft)
    if missing:
        lines.append(
            f"Not on the pages so far: {', '.join(missing)}. If there's another page, send it "
            "before confirming."
        )
    return "\n".join(lines)


def next_question(draft: dict[str, Any]) -> tuple[str, list[str]]:
    for issue in draft["issues"]:
        if not issue["resolved"]:
            return issue["question"], issue["options"]
    return "Everything checked. Confirm to file it and set the reminders?", [CONFIRM, DISCARD]


def answer(draft: dict[str, Any], text: str) -> str:
    """Apply an Admin answer to the first open issue, or confirm/discard. Returns what happened."""
    for issue in draft["issues"]:
        if issue["resolved"]:
            continue
        if issue.get("awaiting_value"):
            set_path(draft["fields"], issue["path"], text.strip())
            issue["resolved"] = True
            return "resolved"
        choice = next((o for o in issue["options"] if o.lower() == text.strip().lower()), None)
        if choice is None:
            return "unmatched"
        if choice in issue["values"]:
            value = issue["values"][choice]
            if issue["kind"] != "conflict":
                set_path(draft["fields"], issue["path"], value)
            elif not issue.get("record"):
                set_path(draft["fields"], issue["path"], _ampm(value))  # this draft's own time
            elif choice.endswith("(this document)"):
                issue["apply_record_time"] = value  # the existing appointment moves on activation
            issue["resolved"] = True
            return "resolved"
        issue["awaiting_value"] = True
        return "awaiting value"
    t = text.strip().lower()
    if t == CONFIRM.lower():
        return "confirm"
    if t == DISCARD.lower():
        draft["status"] = "discarded"
        return "discarded"
    return "unmatched"


# --- activation ------------------------------------------------------------------------------
def _evening_before(d: date, household: dict[str, Any]) -> str:
    return f"{(d - timedelta(days=1)).isoformat()}T{household.get('appointment_reminder', '19:00')}"


def _appointment_label(fields: dict[str, Any], time_text: str) -> str:
    notes = "; ".join(fields.get("instructions") or [])
    where = fields.get("department", "") + (
        f" ({fields['clinic']})" if fields.get("clinic") else ""
    )
    return f"Tomorrow {time_text}: {where}. {notes}".strip()


def _event_id(record_id: str, version: int, at: str) -> str:
    return hashlib.sha1(f"{record_id}:{version}:{at}".encode()).hexdigest()[:16]


def quotes(record: dict[str, Any]) -> tuple[list[str], list[str]]:
    """(excerpt texts, field names) from a record's printed fields: list items one by one, the
    cells of a table row joined with " · ". Values are as transcribed and confirmed."""
    f = record["fields"]
    names = [n for n in record.get("quote", []) if f.get(n)]
    texts = [str(x) for n in names if isinstance(f[n], list) for x in f[n] if str(x).strip()]
    cells = [str(f[n]).strip() for n in names if not isinstance(f[n], list)]
    if any(cells):
        texts.append(" · ".join(c for c in cells if c))
    return texts, names


def excerpt_audience(policy, category: str, names: list[str]) -> list[str]:
    """Roles that may read every quoted field of this category (policy matrix and projections)."""
    roles = []
    for role in policy.roles:
        level, _ = policy.level(role, category)
        allowed = policy.fields_for(role, category, level)
        if level != "none" and (allowed is None or set(names) <= set(allowed)):
            roles.append(role)
    return roles


def activate(
    store: Store, policy, draft: dict[str, Any], household: dict[str, Any], tz: str
) -> dict[str, Any]:
    """File a confirmed draft: records with their excerpts, supersession, events."""
    import json

    f, t = draft["fields"], draft["doc_type"]
    active = {
        json.loads(r["fields"]).get("drug", "").lower(): r
        for r in store.active_records(["medication"])
        if json.loads(r["fields"]).get("directions") and r["assignee"]
    }
    created, superseded, events = [], [], []
    for r in records_for(t, f, household, set(active)):
        same_day = []
        if r.get("kind") == "appointment":  # one appointment a day: the slip is the newer word
            day = parse_date(str(r["fields"].get("date", "")))
            same_day = [
                row
                for row in store.active_records(["appointments"])
                if day and parse_date(str(json.loads(row["fields"]).get("date", ""))) == day
            ]
            if same_day and r.get("from_follow_up"):
                continue  # already on file; a clash in time was asked about in the draft
        texts, names = quotes(r)
        audience = excerpt_audience(policy, r["category"], names)
        excerpt_ids = [
            store.add_excerpt(
                document_id=draft["document_ids"][0],
                text=text,
                category=r["category"],
                audience=audience,
                approved_by=draft["admin"],
            )
            for text in texts
        ]
        rid = store.add_record(
            category=r["category"],
            fields=r["fields"],
            created_by=r.get("created_by") or draft["admin"],
            document_id=draft["document_ids"][0],
            excerpt_ids=excerpt_ids,
            assignee=r.get("assignee"),
        )
        created.append(rid)
        for old in same_day:
            store.supersede(old["id"], rid)
            superseded.append(old["id"])
        rf = r["fields"]
        if r.get("kind") == "schedule":
            old = active.get(rf.get("drug", "").lower())
            if old is not None and old["id"] != rid:
                store.supersede(old["id"], rid)
                superseded.append(old["id"])
            for at in rf.get("times") or []:
                label = med_label(rf)
                if store.add_event(
                    event_id=_event_id(rid, 1, at),
                    record_id=rid,
                    record_version=1,
                    assignee=r["assignee"],
                    kind="daily",
                    at=at,
                    tz=tz,
                    label=label,
                    until=until_of(rf.get("directions", "")),
                ):
                    events.append((r["assignee"], at, label))
        elif r.get("kind") == "appointment":
            d, tm = parse_date(str(rf.get("date", ""))), parse_time(str(rf.get("time", "")))
            if d and tm and r.get("assignee"):
                at, label = _evening_before(d, household), _appointment_label(rf, _ampm(tm))
                if store.add_event(
                    event_id=_event_id(rid, 1, at),
                    record_id=rid,
                    record_version=1,
                    assignee=r["assignee"],
                    kind="once",
                    at=at,
                    tz=tz,
                    label=label,
                ):
                    events.append((r["assignee"], at, label))
        elif r.get("kind") == "dispensing":
            refill = refill_event(rf, household)
            if refill and store.add_event(
                event_id=_event_id(rid, 1, refill[0]),
                record_id=rid,
                record_version=1,
                assignee=draft["admin"],
                kind="once",
                at=refill[0],
                tz=tz,
                label=refill[1],
            ):
                events.append((draft["admin"], refill[0], refill[1]))
    for issue in draft["issues"]:
        if issue.get("apply_record_time") and issue.get("record"):
            _retime_appointment(store, issue["record"], issue["apply_record_time"], household, tz)
    draft["status"] = "confirmed"
    store.save_draft(draft)
    return {"records": created, "superseded": superseded, "events": events}


def refill_event(
    rf: dict[str, Any], household: dict[str, Any], today: date | None = None
) -> tuple[str, str] | None:
    n = per_day(rf.get("directions", ""))
    qty = re.match(r"\s*(\d+)", str(rf.get("quantity", "")))
    dispensed = parse_date(str(rf.get("dispensed", "")))
    if not (n and qty and dispensed):
        return None
    runs_out = dispensed + timedelta(days=int(qty.group(1)) // n - 1)
    ahead = timedelta(days=int(household.get("refill_days_ahead", 3)))
    remind = max(runs_out - ahead, today or date.today())
    label = (
        f"Refill {rf['drug']} {rf.get('strength', '')}: runs out on {show_date(runs_out)} "
        f"(calculated from {rf['quantity']} dispensed {rf['dispensed']}, {n} a day;"
        " not dispensing advice)."
    ).replace("  ", " ")
    return f"{remind.isoformat()}T{household.get('appointment_reminder', '19:00')}", label


def _retime_appointment(
    store: Store, record_id: str, hhmm: str, household: dict[str, Any], tz: str
) -> None:
    """New version of an appointment at another time; its reminder is replaced too."""
    import json

    row = store.record(record_id)
    if row is None or row["category"] != "appointments":
        return
    fields = json.loads(row["fields"])
    fields["time"] = _ampm(hhmm)
    store.supersede(record_id, record_id)  # cancels the old version's reminder
    store.add_record(
        record_id=record_id,
        category="appointments",
        fields=fields,
        created_by=row["created_by"],
        document_id=row["document_id"],
        assignee=row["assignee"],
    )
    version = store.record(record_id)["version"]
    d = parse_date(str(fields.get("date", "")))
    if d and row["assignee"]:
        at, label = _evening_before(d, household), _appointment_label(fields, fields["time"])
        store.add_event(
            event_id=_event_id(record_id, version, at),
            record_id=record_id,
            record_version=version,
            assignee=row["assignee"],
            kind="once",
            at=at,
            tz=tz,
            label=label.strip(),
        )


def household_view(policy, roles: list[str], record_rows: list[Any]) -> list[dict[str, Any]]:
    """What the whole group may see of these records (group level, intersected projections)."""
    import json

    from kin.retrieve import fields_for_all

    out = []
    for row in record_rows:
        level = policy.group_level(row["category"], roles)
        if level == "none":
            continue
        names = fields_for_all(policy, roles, row["category"])
        f = json.loads(row["fields"])
        visible = {k: v for k, v in f.items() if names is None or k in names}
        if visible:
            out.append({"category": row["category"], "fields": visible})
    return out


def group_summary(view: list[dict[str, Any]], title: str, admin_name: str) -> str | None:
    """Fixed-template group post from group-visible fields only; None when nothing is visible."""
    lines, unchanged = [], []
    for r in view:
        f = r["fields"]
        if r["category"] == "medication" and f.get("drug"):
            change = (f.get("change") or "").strip()
            if change.lower() == "unchanged":
                unchanged.append(f["drug"])
            elif (f.get("directions") or "").lower() == "do not take" or change.lower().startswith(
                "stopped"
            ):
                lines.append(
                    f"• {f['drug']}: stopped"
                    + (f" ({change.split(':', 1)[1].strip()})" if ":" in change else "")
                )
            elif f.get("directions"):
                extra = f" ({change})" if change else ""
                lines.append(
                    f"• {f['drug']} {f.get('strength', '')}: {f['directions']}{extra}".replace(
                        "  ", " "
                    )
                )
        elif r["category"] == "appointments" and f.get("date"):
            lines.append(
                f"• Appointment: {f.get('department', '')}, {f['date']}, {f.get('time', '')}"
            )
        elif r["category"] == "medical" and f.get("care_instructions"):
            lines += [f"• {c}" for c in f["care_instructions"]]
    if unchanged:
        lines.append("• Unchanged: " + ", ".join(unchanged))
    if not lines:
        return None
    return f"Update from the {title}, confirmed by {admin_name}:\n" + "\n".join(lines)
