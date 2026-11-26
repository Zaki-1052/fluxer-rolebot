# util/embed.py
EMBED_COLOR = 0x3498DB


def make_embed(text: str) -> dict:
    """Wrap text in an embed dict with the bot's accent color."""
    return {"description": text, "color": EMBED_COLOR}
