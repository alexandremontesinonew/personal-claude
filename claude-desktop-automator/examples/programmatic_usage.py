"""
Example: Programmatic usage of Claude Desktop Automator

This script demonstrates how to use the automator library
in your own Python code.
"""

from claude_automator import Automator
from claude_automator.utils.logger import Logger


def example_basic_usage():
    """Basic usage example."""
    print("Example 1: Basic Usage\n")

    # Initialize automator
    automator = Automator()

    try:
        # Connect to Claude Desktop
        if not automator.initialize():
            print("Failed to initialize. Make sure Claude Desktop is running.")
            return

        # Send a single prompt
        response = automator.send_with_retry("What is Python?")

        if response:
            print(f"Response: {response[:200]}...")  # Print first 200 chars
        else:
            print("Failed to get response")

        # Get statistics
        stats = automator.get_stats()
        print(f"\nSession stats: {stats}")

    finally:
        # Clean up
        automator.stop()


def example_batch_processing():
    """Batch processing example."""
    print("\nExample 2: Batch Processing\n")

    prompts = [
        "Explain list comprehensions in Python",
        "What are Python generators?",
        "How do context managers work?",
    ]

    automator = Automator()

    try:
        if automator.initialize():
            for i, prompt in enumerate(prompts, 1):
                print(f"Processing prompt {i}/{len(prompts)}")
                response = automator.send_with_retry(prompt)

                if response:
                    print(f"✓ Got response ({len(response)} chars)")
                else:
                    print(f"✗ Failed to get response")

            stats = automator.get_stats()
            print(f"\nTotal messages: {stats['total_messages']}")

    finally:
        automator.stop()


def example_context_manager():
    """Using context manager."""
    print("\nExample 3: Context Manager\n")

    with Automator() as automator:
        response = automator.send_with_retry("What is a closure in Python?")
        print(f"Response: {response[:200]}...")

    # Automatically cleaned up
    print("Session saved and closed automatically")


def example_error_handling():
    """Error handling example."""
    print("\nExample 4: Error Handling\n")

    automator = Automator()

    try:
        if not automator.initialize():
            raise Exception("Failed to initialize automator")

        # Send prompt with automatic retry
        max_attempts = 3
        for attempt in range(max_attempts):
            response = automator.send_with_retry("Explain decorators")

            if response:
                print(f"Success on attempt {attempt + 1}")
                break
            else:
                print(f"Attempt {attempt + 1} failed")

                if attempt < max_attempts - 1:
                    print("Retrying...")
        else:
            print("All attempts failed")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        automator.stop()


def example_session_management():
    """Session management example."""
    print("\nExample 5: Session Management\n")

    automator = Automator()

    try:
        automator.initialize()

        # Set custom base instructions
        automator.session.set_base_instructions(
            "You are a Python expert. Provide concise, practical examples."
        )

        # Send prompts
        automator.send_with_retry("Explain list slicing")
        automator.send_with_retry("Show me examples")

        # Save session
        automator.session.save_context(force=True)
        print("Session saved")

        # Get conversation history
        history = automator.session.get_conversation_history(last_n=2)
        print(f"\nLast {len(history)} messages:")
        for msg in history:
            role = msg["role"]
            content = msg["content"]["text"][:50]
            print(f"  {role}: {content}...")

        # Export session
        automator.session.export_session()
        print("\nSession exported")

    finally:
        automator.stop()


def main():
    """Run all examples."""
    # Setup logging
    Logger.setup()

    print("=" * 60)
    print("Claude Desktop Automator - Programmatic Usage Examples")
    print("=" * 60)

    # Uncomment the examples you want to run
    # WARNING: These will actually interact with Claude Desktop!

    # example_basic_usage()
    # example_batch_processing()
    # example_context_manager()
    # example_error_handling()
    # example_session_management()

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
