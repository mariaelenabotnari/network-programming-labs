import asyncio
import uuid
from Lab3.Board import Board
from Lab3.Commands import flip, look

async def main():
    board = await Board.parse_from_file("Board.txt")

    player_id = str(uuid.uuid4())[:8]
    print(f"Player {player_id} starts!\n")

    print("Initial board (everything hidden):")
    print(look(board, player_id))
    print("\n---\n")

    print("Flipping first card (0, 0):")
    flip(player_id, 0, 0, board)
    print(look(board, player_id))
    print("\n---\n")

    print("Flipping second card (0, 1):")
    flip(player_id, 0, 1, board)
    print(look(board, player_id))
    print("\n---\n")

    print("Final board (after flipping two cards):")
    print(board)

if __name__ == "__main__":
    asyncio.run(main())
