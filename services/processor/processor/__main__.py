"""Entry point for AYON List Creator service."""

from .default_handlers.action_create_lists import AyonListCreator


def main():
    """Start the AYON List Creator service."""
    creator = AyonListCreator()
    creator.start()

    print("AYON List Creator service started.")
    print("The service will create lists based on scheduled timers.")
    print("Press Ctrl+C to stop.")

    try:
        # Keep the service running
        import threading
        while True:
            threading.Event().wait(timeout=1)
    except KeyboardInterrupt:
        print("\nStopping AYON List Creator service...")
        creator.stop()
        print("Service stopped.")


if __name__ == "__main__":
    main()
