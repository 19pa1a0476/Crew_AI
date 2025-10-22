import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.sql import text
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from utilities.tools_library import TOOLKIT_LIBRARY
from configuration import PGVectorConfig
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Use the same database connection string from PGVectorConfig
SQLALCHEMY_DATABASE_URL = PGVectorConfig.VECTOR_DB_CONNECTION_STRING

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
# AsyncSessionLocal = async_sessionmaker(bind=async_engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_all_user_agents_and_toolkits(user_id: str, AGENT_LIBRARY, db: Session):
    """
    Initializes all agents in AGENT_LIBRARY and their corresponding toolkits
    with default config values for a given user_id.

    Args:
        user_id (str): External user ID.
        db (Session): SQLAlchemy session.
    """
    for agent_id, agent_data in AGENT_LIBRARY.items():
        tools = agent_data.get("tools", [])

        # 1. Insert user_agent_config if not already present
        insert_agent_query = text("""
            INSERT INTO solution_studio.user_agent_config (
                user_id,
                agent_id,
                enable_memory,
                markdown,
                num_history_runs,
                tools,
                agent_config,
                knowledgebase_details,
                created_at,
                updated_at
            )
            VALUES (
                :user_id,
                :agent_id,
                true, true, 3,
                :tools,
                :agent_config,
                :knowledgebase_details,
                now(), now()
            )
            ON CONFLICT (user_id, agent_id) DO NOTHING;
        """)

        db.execute(insert_agent_query, {
            "user_id": user_id,
            "agent_id": agent_id,
            "tools": json.dumps(tools),
            "agent_config": json.dumps({}),
            "knowledgebase_details": json.dumps([])
        })

        # 2. For each tool in the agent, initialize toolkit config if not already present
        for tool_name in tools:
            if tool_name not in TOOLKIT_LIBRARY:
                continue

            field_keys = [
                field["key"] for field in TOOLKIT_LIBRARY[tool_name].get("config_schema", {}).get("fields", [])
            ]
            config_values = {key: "" for key in field_keys}

            insert_toolkit_query = text("""
                INSERT INTO solution_studio.user_toolkit_config (
                    user_id, tool_name, config_values, created_at, updated_at
                )
                VALUES (
                    :user_id, :tool_name, :config_values, now(), now()
                )
                ON CONFLICT (user_id, tool_name) DO NOTHING;
            """)

            db.execute(insert_toolkit_query, {
                "user_id": user_id,
                "tool_name": tool_name,
                "config_values": json.dumps(config_values)
            })
    db.commit()



def get_user_agent_config(user_id: str, agent_id: str, db: Session) -> Dict[str, Any]:
    query = text("""
        SELECT user_id, agent_id, enable_memory, markdown, num_history_runs,
               tools, agent_config, knowledgebase_details, created_at, updated_at
        FROM solution_studio.user_agent_config
        WHERE user_id = :user_id AND agent_id = :agent_id
    """)
    result = db.execute(query, {"user_id": user_id, "agent_id": agent_id}).fetchone()

    if result is None:
        return {
            "user_id": user_id,
            "agent_id": agent_id,
            "enable_memory": False,
            "markdown": False,
            "num_history_runs": 3,
            "tools": [],
            "agent_config": {},
            "knowledgebase_details": [],
            "created_at": None,
            "updated_at": None
        }

    data = dict(result._mapping)
    for field in ("tools", "agent_config", "knowledgebase_details"):
        if data.get(field):
            data[field] = json.loads(data[field]) if isinstance(data[field], str) else data[field]
        else:
            data[field] = [] if field in ("tools", "knowledgebase_details") else {}

    return data



def upsert_user_agent_config(user_id: str, payload: Dict[str, Any], db: Session):
    """
    Upsert user_agent_config row for the given user_id and payload dictionary.
    Payload must contain:
      - agent_id (str)
      - enable_memory (bool)
      - markdown (bool)
      - num_history_runs (int)
      - tools (list)
      - agent_config (dict)
      - knowledgebase_details (list)
    """
    query = text("""
        INSERT INTO solution_studio.user_agent_config (
            user_id,
            agent_id,
            enable_memory,
            markdown,
            num_history_runs,
            tools,
            agent_config,
            knowledgebase_details,
            created_at,
            updated_at
        )
        VALUES (
            :user_id,
            :agent_id,
            :enable_memory,
            :markdown,
            :num_history_runs,
            :tools,
            :agent_config,
            :knowledgebase_details,
            now(),
            now()
        )
        ON CONFLICT (user_id, agent_id)
        DO UPDATE SET
            enable_memory = EXCLUDED.enable_memory,
            markdown = EXCLUDED.markdown,
            num_history_runs = EXCLUDED.num_history_runs,
            tools = EXCLUDED.tools,
            agent_config = EXCLUDED.agent_config,
            knowledgebase_details = EXCLUDED.knowledgebase_details,
            updated_at = now();
    """)

    db.execute(query, {
        "user_id": user_id,
        "agent_id": payload["agent_id"],
        "enable_memory": payload.get("enable_memory", False),
        "markdown": payload.get("markdown", False),
        "num_history_runs": payload.get("num_history_runs", 3),
        "tools": json.dumps(payload.get("tools", [])),
        "agent_config": json.dumps(payload.get("agent_config", {})),
        "knowledgebase_details": json.dumps(payload.get("knowledgebase_details", [])),
    })
    db.commit()


def update_user_toolkit_config(user_id: str, config_payload: Dict[str, List[Any]], db: Session):
    """
    Updates or inserts toolkit configuration values for a user.

    Args:
        user_id (str): External user ID.
        config_payload (Dict[str, List[ToolkitFieldUpdate]]): Toolkit config fields grouped by tool name.
        db (Session): SQLAlchemy session.
    """
    for tool_name, fields in config_payload.items():
        config_values = {field.key: field.value for field in fields}

        query = text("""
            INSERT INTO solution_studio.user_toolkit_config (user_id, tool_name, config_values, created_at, updated_at)
            VALUES (:user_id, :tool_name, :config_values, now(), now())
            ON CONFLICT (user_id, tool_name)
            DO UPDATE SET
                config_values = EXCLUDED.config_values,
                updated_at = now();
        """)

        db.execute(query, {
            "user_id": user_id,
            "tool_name": tool_name,
            "config_values": json.dumps(config_values)
        })
    db.commit()


def get_knowledgebases(user_id: str, db: Session):
    """
    Returns a list of knowledgebase names for a given user_id
    from solution_studio.knowledgebases using the filters JSON column.
    """
    try:
        query = text("""
            SELECT DISTINCT filters->>'kb_name' AS kb_name
            FROM solution_studio.knowledgebases
            WHERE filters->>'user_id' = :user_id
            AND filters->>'kb_name' IS NOT NULL
        """)

        result = db.execute(query, {"user_id": user_id})
        kb_names = [row[0] for row in result.fetchall()]

        if not kb_names:
            return {"message": "No knowledgebases found for user", "knowledgebases": []}

        return {"message": "Knowledgebases found", "knowledgebases": kb_names}

    except SQLAlchemyError as e:
        print(f"Database error fetching knowledgebases: {str(e)}")
        raise


def delete_knowledgebase(user_id: str, kb_name: str, db: Session):
    """
    Deletes all document records from solution_studio.knowledgebases
    for a given kb_name and user_id.
    """
    try:
        delete_query = text("""
            DELETE FROM solution_studio.knowledgebases
            WHERE filters->>'user_id' = :user_id
            AND filters->>'kb_name' = :kb_name
        """)

        result = db.execute(delete_query, {"user_id": user_id, "kb_name": kb_name})
        db.commit()

        return {
            "status": "success",
            "message": f"Deleted {result.rowcount} document(s) for user_id={user_id}, kb_name={kb_name}"
        }

    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error deleting knowledgebase: {str(e)}")
        raise

# def get_knowledgebases(user_id: str, db: Session):
#     """
#     Returns a list of knowledgebase tables for a given user (schema) using SQLAlchemy session.
#     """
#     try:
#         # 1. Check if schema exists
#         schema_check_query = text("""
#             SELECT EXISTS (
#                 SELECT 1 FROM information_schema.schemata
#                 WHERE schema_name = :schema
#             );
#         """)
#         result = db.execute(schema_check_query, {"schema": user_id})
#         schema_exists = result.scalar()

#         if not schema_exists:
#             return {"message": "No knowledgebases found for user", "knowledgebases": []}

#         # 2. Fetch table names in that schema
#         table_query = text("""
#             SELECT table_name
#             FROM information_schema.tables
#             WHERE table_schema = :schema
#             AND table_type = 'BASE TABLE';
#         """)
#         result = db.execute(table_query, {"schema": user_id})
#         tables = [row[0] for row in result.fetchall()]

#         if not tables:
#             return {"message": "No knowledgebases found for user", "knowledgebases": []}

#         return {"message": "Knowledgebases found", "knowledgebases": tables}
#     except Exception as e:
#         print(f"Error fetching knowledgebases: {str(e)}")
#         raise


def fetch_agent_config(user_id: str, agent_ids: List[str], db: Session) -> Dict[str, Dict[str, Any]]:
    result = {}

    query = text("""
        SELECT agent_id, enable_memory, markdown, num_history_runs, knowledgebase_details
        FROM solution_studio.user_agent_config
        WHERE user_id = :user_id AND agent_id = ANY(:agent_ids)
    """)

    rows = db.execute(query, {"user_id": user_id, "agent_ids": agent_ids})

    for row in rows.fetchall():
        agent_id = row.agent_id
        result[agent_id] = {
            "enable_memory": row.enable_memory,
            "markdown": row.markdown,
            "num_history_runs": row.num_history_runs,
            "knowledgebase_details": row.knowledgebase_details or []
        }
    return result


def fetch_tool_config(user_id: str, tool_names: List[str], db: Session) -> Dict[str, Dict[str, Any]]:
    result = {}

    query = text("""
        SELECT tool_name, config_values
        FROM solution_studio.user_toolkit_config
        WHERE user_id = :user_id AND tool_name = ANY(:tool_names)
    """)

    rows = db.execute(query, {"user_id": user_id, "tool_names": tool_names})

    for row in rows.fetchall():
        result[row.tool_name] = row.config_values

    return result



def sync_kb_deletion(user_id: str, kb_name: str, db: Session):
    """
    Remove kb_name from knowledgebase_details array for all agent configs of the given user_id.

    Args:
        user_id (str): The user ID whose records will be updated.
        kb_name (str): The knowledgebase name to remove.
        db (Session): SQLAlchemy DB session.
    """

    # 1. Fetch all records for the user
    query_select = text("""
        SELECT agent_id, knowledgebase_details
        FROM solution_studio.user_agent_config
        WHERE user_id = :user_id
    """)
    results = db.execute(query_select, {"user_id": user_id}).fetchall()

    # 2. Iterate over records and update if kb_name exists in knowledgebase_details
    for row in results:
        kb_list = row.knowledgebase_details or []
        if isinstance(kb_list, str):
            kb_list = json.loads(kb_list)

        if kb_name in kb_list:
            kb_list.remove(kb_name)

            query_update = text("""
                UPDATE solution_studio.user_agent_config
                SET knowledgebase_details = :new_kb_list,
                    updated_at = now()
                WHERE user_id = :user_id AND agent_id = :agent_id
            """)

            db.execute(query_update, {
                "new_kb_list": json.dumps(kb_list),
                "user_id": user_id,
                "agent_id": row.agent_id
            })

    db.commit()


def create_chat_session(db: Session, session_id: str, user_id: str, title: str = None):
    db.execute(
        text(
        "INSERT INTO solution_studio.chat_session (id, user_id, title, created_at, updated_at) "
        "VALUES (:id, :user_id, :title, :created_at, :updated_at)"),
        {
            "id": session_id,
            "user_id": user_id,
            "title": title,
            "created_at": datetime.now(),
            "updated_at" : datetime.now()
        }
    )


def insert_message(
    db: Session,
    session_id: str,
    user_id: str,
    sender: str,
    message: str,
    attachments: Optional[List[Dict[str, str]]] = None
):
    # Convert Pydantic models to dicts
    if attachments:
        attachments = [a.dict() if hasattr(a, "dict") else a for a in attachments]

    db.execute(
        text("""
            INSERT INTO solution_studio.chat_messages (
                session_id, user_id, sender, message, attachments, timestamp
            ) VALUES (
                :session_id, :user_id, :sender, :message, :attachments, :ts
            )
        """),
        {
            "session_id": session_id,
            "user_id": user_id,
            "sender": sender,
            "message": message,
            "attachments": json.dumps(attachments) if attachments else None,
            "ts": datetime.now()
        }
    )


def fetch_sessions_by_user(db: Session, user_id: str):
    query = text("""
        SELECT id AS session_id, title
        FROM solution_studio.chat_session
        WHERE user_id = :user_id
        ORDER BY updated_at DESC
    """)
    result = db.execute(query, {"user_id": user_id})
    sessions = []
    for row in result.fetchall():
        d = dict(row._mapping)
        # convert datetime to ISO string
        if d.get("updated_at"):
            d["updated_at"] = d["updated_at"].isoformat()
        sessions.append(d)
    return sessions



def fetch_messages_by_user_and_session(db: Session, user_id: str, session_id: str):
    query = text("""
        SELECT sender, message, timestamp, attachments
        FROM solution_studio.chat_messages
        WHERE user_id = :user_id AND session_id = :session_id
        ORDER BY timestamp ASC
    """)
    result = db.execute(query, {"user_id": user_id, "session_id": session_id})
    messages = []
    for row in result.fetchall():
        d = dict(row._mapping)

        # Convert timestamp to ISO string
        if d.get("timestamp"):
            d["timestamp"] = d["timestamp"].isoformat()

        # Process attachments: include only filename
        attachments = d.get("attachments")
        if attachments:
            try:
                # ensure it's a list of dicts and only include filename
                d["attachments"] = [{"filename": item["filename"]} for item in attachments if "filename" in item]
            except Exception:
                d["attachments"] = []
        else:
            d["attachments"] = []
        messages.append(d)
    return messages
