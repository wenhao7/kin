"""Conversations Kin drives itself: intake drafts, the Admin's answers, group posts, sharing.

The Admin is asked one question at a time (kin.prompts: reply-keyboard options, later questions
wait their turn); a tap arrives as ordinary DM text and lands in `handle_prompt`. Nothing reaches
the group or another member without an explicit Admin answer. Other members' only prompt is a
skill's Done.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

from kin import intake, prompts, share, skills
from kin.admin import PICKERS, answer_picker
from kin.context import Context
from kin.extract import classify, extract
from kin.translate import to_mandarin

logger = logging.getLogger("kin.flows")
POST, SKIP = "Post to group", "Don't post"
# Pages sent back to back are extracted in parallel; drafts are created or merged one at a time.
_DRAFTS = threading.Lock()
MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def _admin(ctx: Context):
    return ctx.roster.admin()


def _ask_admin(ctx: Context, kind: str, ref: str, text: str, options: list[str]) -> None:
    prompts.ask(ctx.store, ctx.sender, _admin(ctx), kind, ref, text, options)


def run_intake(ctx: Context, document_id: str) -> None:
    """Background task after the Admin sends a photo: extract, draft, ask."""
    admin = _admin(ctx)
    doc = ctx.store.document(document_id)
    path = ctx.store.originals_dir / (doc["storage_ref"] or "")
    mime = MIME.get(Path(path).suffix.lower())
    if mime is None or not path.is_file():
        ctx.sender.send(admin.telegram_id, "Saved privately, but I can only read photos for now.")
        return
    image = path.read_bytes()
    try:
        doc_type = classify(ctx.client, ctx.model_vision, image, mime)
        if doc_type == "other":
            ctx.sender.send(
                admin.telegram_id, "Saved privately. I couldn't tell what document this is."
            )
            return
        ex = extract(ctx.client, ctx.model_vision, image, mime, doc_type)
    except Exception:  # noqa: BLE001 - the original is kept; the Admin can resend
        logger.exception("extraction failed for %s", document_id)
        ctx.sender.send(
            admin.telegram_id, "Saved privately, but I couldn't read it. Try a clearer photo?"
        )
        return
    with _DRAFTS:
        draft = intake.new_draft(
            ctx.store, admin.id, document_id, ex.doc_type, ex.fields, ex.uncertain
        )
        send_draft(ctx, draft)


def send_draft(ctx: Context, draft: dict) -> None:
    question, options = intake.next_question(draft)
    text = intake.render_draft(draft, ctx.household, ctx.roster) + "\n\n" + question
    _ask_admin(ctx, "draft", draft["id"], text, options)


def handle_prompt(ctx: Context, member, text: str) -> str | None:
    """A member's DM text while a prompt is open; None when it is not an answer (agent turn).
    Kin sends its reply here, before the next waiting question."""
    prompt = ctx.store.current_prompt(member.id)
    if prompt is None:
        return None
    reply = _answer(ctx, member, prompt, text)
    if reply is None and ctx.store.current_prompt(member.id) is not None:
        return None  # not an answer: the question stays open
    if reply:
        ctx.sender.send(member.telegram_id, reply)
    prompts.advance(ctx.store, ctx.sender, member)
    return None if reply is None else ""


def _answer(ctx: Context, member, prompt, text: str) -> str | None:
    if prompt["kind"] in PICKERS:
        return answer_picker(ctx, prompt, text)
    if prompt["kind"] == "skill":
        is_done = text.strip().rstrip(".!").lower() == skills.DONE.lower()
        return skills.done(ctx, member, prompt) if is_done else None
    admin = _admin(ctx)
    if member.id != admin.id:
        return None
    options = json.loads(prompt["options"])
    if prompt["kind"] == "share":
        choice = next((o for o in options if o.lower() == text.strip().lower()), None)
        if choice is None:
            return None
        ctx.store.close_prompt(prompt["id"])
        return share.decide(
            ctx.store, ctx.roster, ctx.sender, int(prompt["ref"]), choice, ctx.group_chat_id
        )
    if prompt["kind"] == "summary":
        if text.strip() not in options:
            return None
        ctx.store.close_prompt(prompt["id"])
        return post_summary(ctx, prompt["ref"]) if text.strip() == POST else "Not posted."
    if prompt["kind"] == "draft":
        draft = ctx.store.draft(prompt["ref"])
        if draft is None or draft["status"] != "open":
            ctx.store.close_prompt(prompt["id"])
            return None
        outcome = intake.answer(draft, text)
        if outcome == "unmatched":
            return None
        ctx.store.save_draft(draft)
        if outcome == "discarded":
            ctx.store.close_prompt(prompt["id"])
            return "Discarded. The photo stays saved privately."
        if outcome == "awaiting value":
            ctx.store.open_prompt(admin.id, "draft", draft["id"], [])
            return "Type the correct value."
        if outcome == "confirm":
            ctx.store.close_prompt(prompt["id"])
            return confirm(ctx, draft)
        send_draft(ctx, draft)  # resolved: show the next question
        return ""
    return None


def confirm(ctx: Context, draft: dict) -> str:
    """Activate a confirmed draft, tell the carer, and offer the group post."""
    result = intake.activate(ctx.store, ctx.policy, draft, ctx.household, ctx.tz)
    rows = [ctx.store.record(rid) for rid in result["records"]]
    _tell_carer(ctx, rows, draft)
    view = intake.household_view(ctx.policy, ctx.store.member_roles(), rows)
    title = intake.source_of(draft["doc_type"], draft["fields"])
    en = intake.group_summary(view, title, _admin(ctx).short)
    lines = [f"Filed {len(result['records'])} records from the {title}."]
    if result["superseded"]:
        lines.append(
            f"Replaced {len(result['superseded'])} older medicine records; their reminders stop."
        )
    if result["events"]:
        lines.append(f"{len(result['events'])} reminders scheduled (/reminders shows them).")
    if en:
        drugs = [json.loads(r["fields"]).get("drug", "") for r in rows if r is not None]
        zh = (
            to_mandarin(ctx.client, ctx.model_super, en, drugs + _names(ctx))
            if _needs_mandarin(ctx) and ctx.client
            else None
        )
        draft["fields"]["_summary"] = {"en": en, "zh": zh, "records": result["records"]}
        ctx.store.save_draft(draft)
        preview = en + (
            f"\n\n{zh}"
            if zh
            else (
                "\n\n(No Mandarin version: the translation failed its check.)"
                if _needs_mandarin(ctx)
                else ""
            )
        )
        ctx.sender.send(_admin(ctx).telegram_id, "\n".join(lines))
        _ask_admin(
            ctx, "summary", draft["id"], f"Post this to the group?\n\n{preview}", [POST, SKIP]
        )
        return ""
    return "\n".join(lines)


def _names(ctx: Context) -> list[str]:
    """People's names stay as written in the Mandarin post, like medicine names."""
    return [n for m in ctx.roster.members for n in (m.short, m.name) if n]


def _needs_mandarin(ctx: Context) -> bool:
    return any(m.language == "zh" for m in ctx.roster.members)


def post_summary(ctx: Context, draft_id: str) -> str:
    draft = ctx.store.draft(draft_id)
    summary = (draft or {}).get("fields", {}).get("_summary")
    if not summary:
        return "Nothing to post."
    result = ctx.sender.send(ctx.group_chat_id, summary["en"])
    if summary.get("zh"):
        ctx.sender.send(ctx.group_chat_id, summary["zh"])
    ctx.store.audit(
        principal=_admin(ctx).id,
        action="group_post",
        decision="approved",
        chat_type="group",
        chat_id=ctx.group_chat_id,
        records=summary.get("records", []),
        destination=ctx.group_chat_id,
        delivery="sent" if result.get("ok") else "failed",
    )
    return "Posted to the group." if result.get("ok") else "I couldn't post to the group."


def _tell_carer(ctx: Context, rows: list, draft: dict) -> None:
    """The new schedule to whoever gives the medicines, in the fields a carer may see."""
    carer = ctx.roster.by_id(ctx.household.get("medicines_by", ""))
    if carer is None or carer.role is None:
        return
    lines = []
    for row in rows:
        if row is None or row["category"] not in ("medication", "medical"):
            continue
        level, _ = ctx.policy.level(carer.role, row["category"])
        names = ctx.policy.fields_for(carer.role, row["category"], level)
        f = {k: v for k, v in json.loads(row["fields"]).items() if names is None or k in names}
        if row["category"] == "medication" and f.get("times"):
            what = f"{f.get('drug', '')} {f.get('strength', '')} — {f.get('directions', '')}"
            lines.append(f"• {', '.join(f['times'])}: {what}")
        elif row["category"] == "medication" and "stop" in str(f.get("change", "")).lower():
            lines.append(f"• Stop {f.get('drug', '')}: {f.get('change', '')}")
        elif row["category"] == "medical":
            lines += [f"• {c}" for c in f.get("care_instructions", [])]
    if not lines:
        return
    title = intake.source_of(draft["doc_type"], draft["fields"])
    text = f"New schedule from the {title}, confirmed by {_admin(ctx).short}:\n" + "\n".join(lines)
    if not carer.telegram_id:
        ctx.sender.send(
            _admin(ctx).telegram_id,
            f"{carer.short} has no Telegram account linked yet, "
            "so the schedule is saved but not sent.",
        )
        return
    result = ctx.sender.send(carer.telegram_id, text)
    ctx.store.audit(
        principal=carer.id,
        action="schedule",
        decision="confirmed",
        records=[r["id"] for r in rows if r is not None],
        destination=carer.telegram_id,
        delivery="sent" if result.get("ok") else "failed",
    )
    if not result.get("ok"):
        ctx.sender.send(
            ctx.group_chat_id,
            f"{carer.short}, please open a chat with me and tap Start "
            "so I can send your reminders.",
        )
