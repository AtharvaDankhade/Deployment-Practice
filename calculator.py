"""Command-line calculator (kept for quick local use).

    python calculator.py

The HTTP API in app/main.py shares the same logic from app/calculator.py.
"""

from app.calculator import OPERATIONS, SYMBOLS, CalculatorError, calculate, format_result

MENU_ORDER = ("add", "subtract", "multiply", "divide")


def show_menu() -> None:
    print("\n=== Simple Calculator ===")
    for i, operation in enumerate(MENU_ORDER, start=1):
        print(f"  {i}. {operation.capitalize()}")
    print("  q. Quit")


def get_number(prompt: str) -> float:
    while True:
        try:
            return float(input(prompt).strip())
        except ValueError:
            print("  Please enter a valid number.")


def main() -> None:
    while True:
        show_menu()
        choice = input("Choose an operation: ").strip().lower()

        if choice in ("q", "quit", "exit"):
            print("Goodbye!")
            return

        if not choice.isdigit() or not 1 <= int(choice) <= len(MENU_ORDER):
            print("  Invalid choice, try again.")
            continue

        operation = MENU_ORDER[int(choice) - 1]
        a = get_number("Enter the first number: ")
        b = get_number("Enter the second number: ")

        try:
            result = calculate(operation, a, b)
        except CalculatorError as err:
            print(f"  Error: {err}")
            continue

        print(f"  Result: {a:g} {SYMBOLS[operation]} {b:g} = {format_result(result)}")


if __name__ == "__main__":
    main()
