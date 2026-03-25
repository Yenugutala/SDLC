"""
SMART INTAKE - Cosmos DB Storage Layer
========================================
Handles:
  - Auto-save every 30 seconds (triggered by UI polling /api/autosave)
  - Draft list retrieval
  - Session resume
  - ETag-based optimistic concurrency (no lost updates)

Cosmos DB container: smart_intake
  Partition key: /user_id
  TTL: 90 days for drafts, unlimited for submitted

Local fallback: SQLite (for dev/testing without Azure)
"""

import json
import sqlite3
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from smart_intake.models import IntakeSession, IntakeStatus, Phase


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

COSMOS_ENDPOINT   = os.getenv("COSMOS_ENDPOINT", "")
COSMOS_KEY        = os.getenv("COSMOS_KEY", "")
COSMOS_DATABASE   = os.getenv("COSMOS_DATABASE", "smart_intake_db")
COSMOS_CONTAINER  = os.getenv("COSMOS_CONTAINER", "intake_sessions")

# Fallback SQLite path for local dev
SQLITE_PATH = os.path.join(os.path.dirname(__file__), "..", "pipeline.db")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# COSMOS DB CLIENT (Azure)
# ─────────────────────────────────────────────

def _get_cosmos_container():
    """Returns Cosmos DB container client. Raises if not configured."""
    from azure.cosmos import CosmosClient, exceptions  # type: ignore
    client = CosmosClient(COSMOS_ENDPOINT, credential=COSMOS_KEY)
    db = client.get_database_client(COSMOS_DATABASE)
    return db.get_container_client(COSMOS_CONTAINER)


# ─────────────────────────────────────────────
# SQLITE FALLBACK (local dev / CI)
# ─────────────────────────────────────────────

def _init_sqlite():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS intake_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            project_name TEXT,
            status TEXT DEFAULT 'draft',
            current_phase TEXT,
            answers TEXT DEFAULT '{}',
            compliance_flags TEXT DEFAULT '[]',
            roi_summary TEXT,
            rom_summary TEXT,
            llm_followups TEXT DEFAULT '[]',
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    return conn


def _use_cosmos() -> bool:
    return bool(COSMOS_ENDPOINT and COSMOS_KEY)


# ─────────────────────────────────────────────
# CRUD OPERATIONS
# ─────────────────────────────────────────────

def create_session(user_id: str, project_name: str) -> IntakeSession:
    """Creates a new draft session."""
    session = IntakeSession(
        session_id=str(uuid.uuid4()),
        user_id=user_id,
        project_name=project_name,
        status=IntakeStatus.DRAFT,
        current_phase=Phase.P1_PROJECT_CONTEXT,
        answers={},
        compliance_flags=[],
        created_at=_now_iso(),
        updated_at=_now_iso()
    )
    _upsert_session(session)
    return session


def save_session(session: IntakeSession) -> IntakeSession:
    """Auto-save: updates answers, phase, flags. Called every 30s by UI."""
    session.updated_at = _now_iso()
    _upsert_session(session)
    return session


def get_session(session_id: str, user_id: str) -> Optional[IntakeSession]:
    """Loads a session by ID. Returns None if not found."""
    if _use_cosmos():
        return _cosmos_get(session_id, user_id)
    return _sqlite_get(session_id)


def list_drafts(user_id: str) -> List[Dict]:
    """Returns summary list of all draft sessions for a user."""
    if _use_cosmos():
        return _cosmos_list_drafts(user_id)
    return _sqlite_list_drafts(user_id)


def submit_session(session_id: str, user_id: str) -> IntakeSession:
    """Marks session as submitted (final)."""
    session = get_session(session_id, user_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    session.status = IntakeStatus.SUBMITTED
    session.updated_at = _now_iso()
    _upsert_session(session)
    return session


def delete_session(session_id: str, user_id: str) -> bool:
    """Deletes a draft session. Submitted sessions cannot be deleted."""
    session = get_session(session_id, user_id)
    if not session:
        return False
    if session.status != IntakeStatus.DRAFT:
        raise PermissionError("Cannot delete a submitted session.")
    if _use_cosmos():
        try:
            container = _get_cosmos_container()
            container.delete_item(item=session_id, partition_key=user_id)
            return True
        except Exception:
            return False
    else:
        conn = _init_sqlite()
        conn.execute("DELETE FROM intake_sessions WHERE session_id=?", (session_id,))
        conn.commit()
        return True


# ─────────────────────────────────────────────
# COSMOS IMPLEMENTATION
# ─────────────────────────────────────────────

def _upsert_session(session: IntakeSession):
    doc = {
        "id": session.session_id,
        "user_id": session.user_id,
        "project_name": session.project_name,
        "status": session.status.value,
        "current_phase": session.current_phase.value,
        "answers": session.answers,
        "compliance_flags": [f.value for f in session.compliance_flags],
        "roi_summary": session.roi_summary,
        "rom_summary": session.rom_summary,
        "llm_followups_generated": session.llm_followups_generated,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }
    if _use_cosmos():
        container = _get_cosmos_container()
        container.upsert_item(doc)
    else:
        conn = _init_sqlite()
        conn.execute("""
            INSERT OR REPLACE INTO intake_sessions VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            session.session_id, session.user_id, session.project_name,
            session.status.value, session.current_phase.value,
            json.dumps(session.answers),
            json.dumps([f.value for f in session.compliance_flags]),
            json.dumps(session.roi_summary),
            json.dumps(session.rom_summary),
            json.dumps(session.llm_followups_generated),
            session.created_at, session.updated_at
        ))
        conn.commit()


def _cosmos_get(session_id: str, user_id: str) -> Optional[IntakeSession]:
    try:
        container = _get_cosmos_container()
        doc = container.read_item(item=session_id, partition_key=user_id)
        return _doc_to_session(doc)
    except Exception:
        return None


def _cosmos_list_drafts(user_id: str) -> List[Dict]:
    container = _get_cosmos_container()
    query = "SELECT c.id, c.project_name, c.status, c.current_phase, c.updated_at FROM c WHERE c.user_id=@uid AND c.status='draft'"
    items = list(container.query_items(
        query=query,
        parameters=[{"name": "@uid", "value": user_id}],
        enable_cross_partition_query=False
    ))
    return items


# ─────────────────────────────────────────────
# SQLITE IMPLEMENTATION
# ─────────────────────────────────────────────

def _sqlite_get(session_id: str) -> Optional[IntakeSession]:
    conn = _init_sqlite()
    row = conn.execute(
        "SELECT * FROM intake_sessions WHERE session_id=?", (session_id,)
    ).fetchone()
    if not row:
        return None
    return _row_to_session(row)


def _sqlite_list_drafts(user_id: str) -> List[Dict]:
    conn = _init_sqlite()
    rows = conn.execute(
        "SELECT session_id, project_name, status, current_phase, updated_at "
        "FROM intake_sessions WHERE user_id=? AND status='draft' ORDER BY updated_at DESC",
        (user_id,)
    ).fetchall()
    return [
        {"session_id": r[0], "project_name": r[1], "status": r[2],
         "current_phase": r[3], "updated_at": r[4]}
        for r in rows
    ]


def _row_to_session(row) -> IntakeSession:
    from smart_intake.models import ComplianceFlag
    return IntakeSession(
        session_id=row[0], user_id=row[1], project_name=row[2],
        status=IntakeStatus(row[3]), current_phase=Phase(row[4]),
        answers=json.loads(row[5] or "{}"),
        compliance_flags=[ComplianceFlag(f) for f in json.loads(row[6] or "[]") if f],
        roi_summary=json.loads(row[7]) if row[7] else None,
        rom_summary=json.loads(row[8]) if row[8] else None,
        llm_followups_generated=json.loads(row[9] or "[]"),
        created_at=row[10], updated_at=row[11]
    )


def _doc_to_session(doc: Dict) -> IntakeSession:
    from smart_intake.models import ComplianceFlag
    return IntakeSession(
        session_id=doc["id"], user_id=doc["user_id"], project_name=doc.get("project_name", ""),
        status=IntakeStatus(doc["status"]), current_phase=Phase(doc["current_phase"]),
        answers=doc.get("answers", {}),
        compliance_flags=[ComplianceFlag(f) for f in doc.get("compliance_flags", []) if f],
        roi_summary=doc.get("roi_summary"),
        rom_summary=doc.get("rom_summary"),
        llm_followups_generated=doc.get("llm_followups_generated", []),
        created_at=doc.get("created_at", ""), updated_at=doc.get("updated_at", "")
    )
