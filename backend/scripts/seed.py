"""Standalone seeding script: `uv run python scripts/seed.py`."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.application.services.seed_service import SeedService  # noqa: E402
from app.infra.database.mongodb import close_client, ensure_indexes, get_db  # noqa: E402


async def main() -> None:
    db = get_db()
    await ensure_indexes(db)
    result = await SeedService(db).seed()
    print(json.dumps(result, indent=2, default=str))
    await close_client()


if __name__ == "__main__":
    asyncio.run(main())
