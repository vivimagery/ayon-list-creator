"""Entry point for AYON List Creator service."""

from .default_handlers.action_create_lists import AyonListCreator


def main():
    """Start the AYON List Creator service."""
    creator = AyonListCreator()
    creator.start()

    try:
        # Keep the service running
        import threading
        while True:
            threading.Event().wait(timeout=1)
    except KeyboardInterrupt:
        creator.stop()


if __name__ == "__main__":
    main()
