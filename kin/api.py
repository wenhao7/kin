"""kin API, used only by the Kin plugin inside Hermes (compose network; `KIN_API_TOKEN`).

Every request carries `caller` as the gateway supplied it. Tool endpoints take no identity of
their own: whatever a model passes in a tool's arguments, only `caller` decides the principal.
`/outbound` sees every final reply before Hermes sends it (kin.answer).
"""

from __future__ import annotations

import base64
import hmac
from typing import Any

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from kin import answer, flows, lookup
from kin.context import Context
from kin.inbound import Inbound, decide
from kin.retrieve import Caller, Refused, principal_for, retrieve

MAX_UPLOAD = 15 * 1024 * 1024


class CallerIn(BaseModel):
    platform: str
    user_id: str
    chat_id: str
    chat_type: str
    message_id: str | None = None

    def to_caller(self) -> Caller:
        if self.platform != "telegram" or not self.user_id:
            raise HTTPException(403, "Kin serves the family's Telegram chats only")
        return Caller(user_id=self.user_id, chat_id=self.chat_id, chat_type=self.chat_type)


class InboundIn(BaseModel):
    caller: CallerIn
    kind: str
    text: str = ""
    reply_to_kin: bool = False
    reply_to_bot: str = ""  # username of the bot the message replies to, if any
    file_b64: str | None = None
    filename: str | None = None


class AskIn(BaseModel):
    caller: CallerIn
    question: str = Field(default="", max_length=2000)


class NoteIn(BaseModel):
    caller: CallerIn
    text: str = Field(min_length=1, max_length=2000)


class LookupIn(BaseModel):
    caller: CallerIn
    topic: str = Field(default="", max_length=500)


class OutboundIn(BaseModel):
    caller: CallerIn
    text: str = Field(default="", max_length=20000)


def create_app(ctx: Context, token: str) -> FastAPI:
    app = FastAPI(title="kin", docs_url=None, redoc_url=None, openapi_url=None)
    store, policy, sender = ctx.store, ctx.policy, ctx.sender
    group_chat_id = ctx.group_chat_id  # the roster is ctx.roster: the judge demo rebuilds it

    def authorised(authorization: str = Header(default="")) -> None:
        expected = f"Bearer {token}"
        if not token or not hmac.compare_digest(authorization.encode(), expected.encode()):
            raise HTTPException(401, "unauthorised")

    def principal(caller: CallerIn):
        try:
            return principal_for(caller.to_caller(), ctx.roster, group_chat_id)
        except Refused as exc:
            raise HTTPException(403, str(exc)) from exc

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/inbound", dependencies=[Depends(authorised)])
    def inbound(body: InboundIn, background: BackgroundTasks) -> dict[str, Any]:
        content = None
        if body.file_b64:
            content = base64.b64decode(body.file_b64)
            if len(content) > MAX_UPLOAD:
                raise HTTPException(413, "file too large")
        msg = Inbound(
            caller=body.caller.to_caller(),
            kind=body.kind,
            text=body.text,
            message_id=body.caller.message_id,
            reply_to_kin=body.reply_to_kin
            or bool(body.reply_to_bot)
            and body.reply_to_bot.lower() == sender.username().lower(),
            content=content,
            filename=body.filename,
        )
        decision = decide(ctx, msg, sender.username())
        if decision.action == "pass":
            ctx.turns.begin(msg.caller, msg.text)  # an agent turn starts: nothing returned yet
        if decision.intake:
            background.add_task(flows.run_intake, ctx, decision.intake)
        delivery = None
        if decision.reply:
            delivery = sender.send(
                body.caller.chat_id,
                decision.reply,
                reply_to=msg.message_id,
                remove_keyboard=decision.remove_keyboard,
            )
        store.audit(
            principal=ctx.roster.by_telegram_id(body.caller.user_id).id,
            action=f"inbound:{body.kind}",
            decision=decision.reason,
            chat_type=body.caller.chat_type,
            chat_id=body.caller.chat_id,
            delivery=None if delivery is None else ("sent" if delivery["ok"] else "failed"),
        )
        out = {"action": decision.action, "reason": decision.reason}
        if decision.reset_sessions:
            out["reset"] = True
        return out

    @app.post("/tools/ask", dependencies=[Depends(authorised)])
    def ask(body: AskIn) -> dict[str, Any]:
        p = principal(body.caller)
        result = retrieve(store, policy, p, body.question)
        ctx.turns.add(body.caller.to_caller(), records=[r["id"] for r in result.records])
        admin = ctx.roster.admin()
        rules = answer.rules(ctx.household, admin.short if admin else "", p.chat_type == "group")
        return {"records": result.records, "rules": rules}

    @app.post("/tools/lookup", dependencies=[Depends(authorised)])
    def lookup_tool(body: LookupIn) -> dict[str, Any]:
        p = principal(body.caller)
        if p.member.role is None:
            return {"error": "Kin answers only the family's members."}
        topic = lookup.match(ctx.locale, body.topic)
        if topic is None:
            names = [t["name"] for t in lookup.topics(ctx.locale)]
            store.audit(principal=p.member.id, action="lookup", decision="no topic")
            return {"error": "Not a public scheme Kin can look up.", "schemes": names}
        if ctx.search is None:
            return {"error": "Public lookups are not set up."}
        query = lookup.query_for(topic)
        try:
            results = lookup.search(ctx.search, ctx.locale, topic)
        except Exception:  # noqa: BLE001 - nothing personal was sent; say it failed
            results = None
        store.audit(
            principal=p.member.id,
            action="lookup",
            decision="failed" if results is None else ("allowed" if results else "empty"),
            chat_type=p.chat_type,
            chat_id=p.chat_id,
            query=query,
            destination=p.chat_id,
        )
        if results is None:
            return {"error": "The lookup failed. Try again later."}
        sources = [{"title": r["title"], "url": r["url"]} for r in results]
        ctx.turns.add(body.caller.to_caller(), sources=sources)
        rules = lookup.LOOKUP_RULES + (answer.GROUP_RULE if p.chat_type == "group" else "")
        return {"scheme": topic["name"], "results": results, "rules": rules}

    @app.post("/outbound", dependencies=[Depends(authorised)])
    def outbound(body: OutboundIn) -> dict[str, str]:
        caller = body.caller.to_caller()
        try:
            p = principal_for(caller, ctx.roster, group_chat_id)
        except Refused:
            return {"text": answer.WITHHELD, "decision": "refused"}
        if p.member.role is None:
            return {"text": answer.WITHHELD, "decision": "unknown sender"}
        text, decision = answer.finish(ctx, caller, p, body.text)
        return {"text": text, "decision": decision}

    @app.post("/tools/note", dependencies=[Depends(authorised)])
    def note(body: NoteIn) -> dict[str, Any]:
        p = principal(body.caller)
        level = policy.level(p.member.role, "notes")[0] if p.member.role else "none"
        if level != "write":
            store.audit(principal=p.member.id, action="note", decision="refused")
            return {"saved": False, "reason": "You can't save notes here."}
        record_id = store.add_record(
            category="notes", fields={"text": body.text}, created_by=p.member.id
        )
        store.audit(
            principal=p.member.id,
            action="note",
            decision="saved",
            records=[record_id],
            chat_type=p.chat_type,
            chat_id=p.chat_id,
        )
        return {"saved": True, "note": record_id}

    return app
