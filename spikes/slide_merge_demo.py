"""Interactive 4×4 console demo for the 2048 slide/merge algorithm.

Runs a full game loop using keyboard input (w/a/s/d/q) on a 4×4 grid.
Demonstrates the slide_merge algorithm from spikes.slide_merge.
Only uses stdlib imports plus spikes.slide_merge — zero pygame.

Usage:
    poetry run python spikes/slide_merge_demo.py
"""

# CHANGELOG:
# - Sprint 2: Created interactive console demo for slide/merge algorithm

import os
import random
import sys

# Ensure the project root is on sys.path so 'spikes.slide_merge' resolves
# when running as a standalone script: python spikes/slide_merge_demo.py
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from spikes.slide_merge import Direction, slide_merge  # noqa: E402 — sys.path setup above


# ---------------------------------------------------------------------------
# Grid helpers
# ---------------------------------------------------------------------------


def create_empty_grid() -> list[list[int]]:
    """Create a 4×4 grid of zeros."""
    return [[0 for _ in range(4)] for _ in range(4)]


def spawn_tile(grid: list[list[int]]) -> None:
    """Place a random 2 or 4 in a random empty cell. Mutates grid in place.

    90% chance of 2, 10% chance of 4 (standard 2048 convention).
    Silently returns if no empty cells exist.

    Args:
        grid: The 4×4 game grid to mutate.
    """
    empty_cells = [
        (row, col) for row in range(4) for col in range(4) if grid[row][col] == 0
    ]
    if not empty_cells:
        return
    row, col = random.choice(empty_cells)
    value = random.choice([2, 2, 2, 2, 2, 2, 2, 2, 2, 4])
    grid[row][col] = value


def has_empty_cells(grid: list[list[int]]) -> bool:
    """Return True if any cell in the grid is 0.

    Args:
        grid: The 4×4 game grid.

    Returns:
        True if at least one cell is zero (empty).
    """
    return any(cell == 0 for row in grid for cell in row)


def is_game_over(grid: list[list[int]]) -> bool:
    """Return True if no valid move exists in any direction.

    Tries all four slide directions. If none produces a grid change,
    the game is over.

    Args:
        grid: The 4×4 game grid.

    Returns:
        True if no direction produces a board change.
    """
    for direction in Direction:
        result = slide_merge(grid, direction)
        new_grid = result.grid
        if new_grid != grid:
            return False
    return True


# ---------------------------------------------------------------------------
# Display helpers
# ---------------------------------------------------------------------------


def format_row(row: list[int]) -> str:
    """Format a single grid row as a pipe-separated, aligned string.

    Args:
        row: A list of 4 integer cell values.

    Returns:
        A string like "   2 |    . |    . |   16".
    """
    cells = [f"{v:>4}" if v != 0 else "   ." for v in row]
    return " | ".join(cells)


def display_grid(grid: list[list[int]], score: int) -> None:
    """Clear the screen and print the 4×4 grid with current score.

    Uses os.system('cls') for Windows screen clearing.

    Args:
        grid: The 4×4 game grid.
        score: Cumulative score to display.
    """
    os.system("cls")

    print("=== 2048 Slide/Merge Demo ===")
    print()
    for row in grid:
        print(format_row(row))
    print()
    print(f"Score: {score}")
    print("Move: w=UP a=LEFT s=DOWN d=RIGHT | q=Quit")


# ---------------------------------------------------------------------------
# Input
# ---------------------------------------------------------------------------


def get_move() -> str:
    """Read a single-character move command from stdin.

    Returns:
        One of 'w', 'a', 's', 'd', 'q', or 'q' on EOF.
    """
    try:
        raw = input("Your move: ")
    except EOFError:
        return "q"
    if not raw:
        return ""
    return raw[0].lower()


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the full 2048 game loop.

    Three exit paths:
    - Player presses 'q' → clean quit with goodbye message.
    - No valid moves remain → GAME OVER display.
    - Ctrl+C → KeyboardInterrupt caught, goodbye printed.
    """
    try:
        grid = create_empty_grid()
        score = 0
        spawn_tile(grid)
        spawn_tile(grid)

        while True:
            display_grid(grid, score)
            move = get_move()

            if move == "q":
                print(f"\nThanks for playing! Final score: {score}")
                return

            if move not in ("w", "a", "s", "d"):
                print("Invalid key. Use w/a/s/d to move, q to quit.")
                continue

            direction = {
                "w": Direction.UP,
                "a": Direction.LEFT,
                "s": Direction.DOWN,
                "d": Direction.RIGHT,
            }[move]

            result = slide_merge(grid, direction)
            new_grid = result.grid
            move_score = result.score

            if new_grid == grid:
                print("No valid move in that direction.")
                continue

            grid = new_grid
            score += move_score
            spawn_tile(grid)

            if is_game_over(grid):
                display_grid(grid, score)
                print("\nGAME OVER! No more valid moves.")
                print(f"Final score: {score}")
                return

    except KeyboardInterrupt:
        print("\n\nThanks for playing!")


if __name__ == "__main__":
    main()