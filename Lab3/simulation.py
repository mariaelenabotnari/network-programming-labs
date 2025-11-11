import asyncio
import random
import time
from Lab3.Board import Board
from Lab3.Card import Card
from Lab3.CommandsImpl import Commands


async def random_player(player_id: str, cmds: Commands, rows: int, cols: int, num_moves: int):
    """
    Simulates a single player making num_moves random flip attempts.
    Sleeps 0.1ms–2ms between attempts.
    Counts successes (flip returned normally) and failures (rule exceptions).
    Returns a stats dict for this player.
    """
    start = time.perf_counter()
    successes = 0
    failures = 0

    for _ in range(num_moves):
        await asyncio.sleep(random.uniform(0.0001, 0.002))  # 0.1ms - 2ms between moves

        r = random.randint(0, rows - 1)
        c = random.randint(0, cols - 1)

        try:
            await cmds.flip(player_id, r, c)
            successes += 1
        except Exception:
            failures += 1

    elapsed = time.perf_counter() - start
    return {
        "player": player_id,
        "attempted": num_moves,
        "successes": successes,
        "failures": failures,
        "elapsed_s": elapsed,
    }


async def run_stress_test():
    print("Starting deterministic stress test simulation...")

    # --- Build a fixed 4x4 board  ---
    board = Board()
    board.nr_rows = 4
    board.nr_cols = 4

    values = [
        "A", "A", "B", "B",
        "C", "C", "D", "D",
        "E", "E", "F", "F",
        "G", "G", "H", "H"
    ]

    cards = []
    i = 0
    for r in range(4):
        row = []
        for c in range(4):
            row.append(Card(values[i]))
            i += 1
        cards.append(row)

    board.cards = cards
    cmds = Commands(board)

    nr_players = 4
    moves_per_player = 100

    # --- Launch players concurrently ---
    start_time = time.perf_counter()
    tasks = [
        random_player(f"Player_{i}", cmds, 4, 4, moves_per_player)
        for i in range(nr_players)
    ]

    try:
        results = await asyncio.gather(*tasks)
    except Exception as unexpected:
        print(f"\nTest FAILED: unexpected crash: {unexpected}")
        return

    final_time = time.perf_counter() - start_time
    print("\nSimulation finished with no unexpected crashes.")

    # --- Verify final board integrity ---
    try:
        board.checkRep()
        print("Final board.checkRep() PASSED.")
    except AssertionError as e:
        print(f"Final board.checkRep() FAILED: {e}")

    # --- Print per-player and aggregate stats ---
    total_attempted = sum(r["attempted"] for r in results)
    total_successes = sum(r["successes"] for r in results)
    total_failures = sum(r["failures"] for r in results)

    print("\n=== Per-player stats ===")
    for r in results:
        rate = (r["successes"] / r["attempted"]) * 100 if r["attempted"] else 0.0
        print(
            f"{r['player']}: "
            f"attempted={r['attempted']}, successes={r['successes']}, failures={r['failures']} "
            f"({rate:.1f}% success), time={r['elapsed_s']:.3f}s"
        )

    print("\n=== Aggregate stats ===")
    overall_rate = (total_successes / total_attempted) * 100 if total_attempted else 0.0
    print(f"players={nr_players}, attempted={total_attempted}, successes={total_successes}, failures={total_failures} ({overall_rate:.1f}% success)")
    print(f"overall wall time={final_time:.3f}s")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
