from miles.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger("miles.bonus_alert_bot")

def main():
    try:
        # ... existing bot startup and loop ...
        pass
    except Exception as e:
        logger.exception("Fatal error in main bot loop")
        # Optionally: notify admin via Telegram here

if __name__ == "__main__":
    main()