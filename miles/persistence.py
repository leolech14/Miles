from typing import Any
from miles.db import get_conn


class Promotion:
    """Placeholder for Promotion model"""

    canonical_id: str
    source_program: str
    target_program: str
    bonus_percent: int
    start_date: Any
    end_date: Any
    url: str
    raw_title: str


async def save_promo(p: Promotion, duplicate: bool) -> None:
    """
    Store every promotion.  If `duplicate` is True we upsert only the
    discovered_at timestamp so we can later compute longevity.
    """
    sql = """
    INSERT INTO promotions (canonical_id, source_program, target_program,
            bonus_percent, start_date, end_date, src_url, raw_title)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
    ON CONFLICT (canonical_id) DO UPDATE
       SET discovered_at = NOW()
    """
    async with await get_conn() as conn:
        await conn.execute(
            sql,
            p.canonical_id,
            p.source_program,
            p.target_program,
            p.bonus_percent,
            p.start_date,
            p.end_date,
            p.url,
            p.raw_title,
        )
