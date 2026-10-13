"""kin API, used only by the Kin plugin inside Hermes (compose network; `KIN_API_TOKEN`).

Every request carries `caller` as the gateway supplied it. Tool endpoints take no identity of
their own: whatever a model passes in a tool's arguments, only `caller` decides the principal.
"""

from __future__ import annotations

import base64
import hmac
from typing import Any, Protocol

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from kin.inbound import Inbound, decide
from kin.members import Roster
from kin.policy import Policy
from kin.retrieve import Caller, Refused, principal_for, retrieve
from kin.store import Store

ANSWER_RULES = (
    "Answer only from these records, which are all this person may see in this chat. "
    "Name the source (document and date) for every statement about the person being cared for, "
    "and quote excerpts word for word. If nothing here answers the question, say you don't know. "
    "Never mention or guess at anything not listed. Organise, never advise: no diagnosis, dosing "
    "or interpretation."
)
MAX_UPLOAD = 15 * 1024 * 1024


class Sender(Protocol):
    def send(
        self,
        chat_id: str,
        text: str,
        reply_to: str | None = None,
        keyboard: list[str] | None = None,
    ) -> dict[str, Any]: ...

    def username(self) -> str: ...


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
    file_b64: str | None = None
    filename: str | None = None


class AskIn(BaseModel):
    caller: CallerIn
    question: str = Field(default="", max_length=2000)


class NoteIn(BaseModel):
    caller: CallerIn
    text: str = Field(min_length=1, max_length=2000)


def create_app(
    *, store: Store, policy: Policy, roster: Roster, sender: Sender, group_chat_id: str, token: str
) -> FastAPI:
    app = FastAPI(title="kin", docs_url=None, redoc_url=None, openapi_url=None)

    def authorised(authorization: str = Header(default="")) -> None:
        expected = f"Bearer {token}"
        if not token or not hmac.compare_digest(authorization.encode(), expected.encode()):
            raise HTTPException(401, "unauthorised")

    def principal(caller: CallerIn):
        try:
            return principal_for(caller.to_caller(), roster, group_chat_id)
        except Refused as exc:
            raise HTTPException(403, str(exc)) from exc

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.post("/inbound", dependencies=[Depends(authorised)])
    def inbound(body: InboundIn) -> dict[str, str]:
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
            reply_to_kin=body.reply_to_kin,
            content=content,
            filename=body.filename,
        )
        decision = decide(store, roster, group_chat_id, msg, sender.username())
        delivery = None
        if decision.reply:
            delivery = sender.send(body.caller.chat_id, decision.reply, reply_to=msg.message_id)
        store.audit(
            principal=roster.by_telegram_id(body.caller.user_id).id,
            action=f"inbound:{body.kind}",
            decision=decision.reason,
            chat_type=body.caller.chat_type,
            chat_id=body.caller.chat_id,
            delivery=None if delivery is None else ("sent" if delivery["ok"] else "failed"),
        )
        return {"action": decision.action, "reason": decision.reason}

    @app.post("/tools/ask", dependencies=[Depends(authorised)])
    def ask(body: AskIn) -> dict[str, Any]:
        result = retrieve(store, policy, principal(body.caller), body.question)
        return {"records": result.records, "rules": ANSWER_RULES}

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
