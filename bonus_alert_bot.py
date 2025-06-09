#!/usr/bin/env python3
"""Entry point for bonus alert bot - delegates to miles.bonus_alert_bot"""

from miles.bonus_alert_bot import main

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
