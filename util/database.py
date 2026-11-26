# util/database.py
from tinydb import TinyDB, Query
import os
import time

Database = TinyDB(os.getenv("DB_PATH", "db.json"))
roles_table = Database.table("roles")
message_table = Database.table("message")


def set_configured_message(
    guild_id: int, channel_id: int, message_id: int
) -> None:
    """Store a configured message. Multiple messages per guild are allowed."""
    Row = Query()
    message_table.upsert(
        {
            "guild_id": guild_id,
            "channel_id": channel_id,
            "configured_message_id": message_id,
            "created_at": time.time(),
        },
        (Row.guild_id == guild_id) & (Row.configured_message_id == message_id),
    )


def get_latest_configured_message(guild_id: int) -> dict | None:
    """Return the most recently configured message for a guild, or None."""
    Row = Query()
    results = message_table.search(
        (Row.guild_id == guild_id) & (Row.configured_message_id.exists())
    )
    if not results:
        return None
    # Rows written before multi-message support have no created_at.
    # Treat them as the oldest so new messages take priority.
    results.sort(key=lambda r: r.get("created_at", 0), reverse=True)
    return {
        "channel_id": results[0]["channel_id"],
        "message_id": results[0]["configured_message_id"],
    }


def is_configured_message(guild_id: int, message_id: int) -> bool:
    """Check if a message is any configured reaction-role message for the guild."""
    Row = Query()
    return bool(
        message_table.search(
            (Row.guild_id == guild_id) & (Row.configured_message_id == message_id)
        )
    )


def delete_configured_message(guild_id: int, message_id: int) -> bool:
    """Delete a specific configured message and all its role associations."""
    Row = Query()
    removed = message_table.remove(
        (Row.guild_id == guild_id) & (Row.configured_message_id == message_id)
    )
    # Cascade: remove role associations tied to this message.
    roles_table.remove(
        (Row.guild_id == guild_id) & (Row.message_id == message_id)
    )
    return len(removed) > 0


def set_role_association(
    guild_id: int, message_id: int, role_id: int, emoji: str
) -> None:
    """Associate an emoji with a role on a specific message."""
    Row = Query()
    roles_table.upsert(
        {
            "guild_id": guild_id,
            "message_id": message_id,
            "role_id": role_id,
            "emoji": emoji,
        },
        (Row.guild_id == guild_id)
        & (Row.message_id == message_id)
        & (Row.emoji == emoji),
    )


def get_role_association(
    guild_id: int, message_id: int, emoji: str
) -> int | None:
    """Get the role ID for an emoji on a specific message.

    Rows written before multi-message support have no message_id.
    Those rows match any message in the guild so existing setups keep working
    until the admin re-runs !add, which writes the message_id.
    """
    Row = Query()
    # Try exact match first (new-format rows).
    result = roles_table.search(
        (Row.guild_id == guild_id)
        & (Row.message_id == message_id)
        & (Row.emoji == emoji)
    )
    if result:
        return result[0]["role_id"]
    # Fall back to legacy rows that have no message_id.
    result = roles_table.search(
        (Row.guild_id == guild_id)
        & (~Row.message_id.exists())
        & (Row.emoji == emoji)
    )
    return result[0]["role_id"] if result else None


def delete_role_association(
    guild_id: int, message_id: int, emoji: str
) -> bool:
    """Remove an emoji-role association from a specific message."""
    Row = Query()
    removed = roles_table.remove(
        (Row.guild_id == guild_id)
        & (Row.message_id == message_id)
        & (Row.emoji == emoji)
    )
    return len(removed) > 0
