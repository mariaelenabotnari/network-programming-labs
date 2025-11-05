import asyncio
from typing import List, Optional


class Card:
    def __init__(self, string_value: str, face_down: bool = True,
                 face_up: bool = False, removed: bool = False, player_id: Optional[str] = None):
        self.string_value = string_value
        self.face_down = face_down
        self.face_up = face_up
        self.removed = removed
        self.player_id = player_id

    def __str__(self):
        if self.removed:
            return "_"
        elif self.face_up:
            return self.string_value
        else:
            return "*"


class Board:
    nr_cols: int
    nr_rows: int
    cards: List[List['Card']]

    def __init__(self):
        self.player_state = {}
        self.nr_cols = 0
        self.nr_rows = 0
        self.cards = []
        self.watchers: list[asyncio.Future] = []

    def notify_watchers(self):
        for watcher in self.watchers:
            if not watcher.done():
                watcher.set_result(True)
        self.watchers.clear()

    async def wait_for_change(self):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self.watchers.append(future)
        await future

    def get_card(self, row: int, col: int):
        return self.cards[row][col]

    def __str__(self):
        board_rows = []
        for r in range(self.nr_rows):
            row_string = " ".join(str(self.cards[r][c]) for c in range(self.nr_cols))
            board_rows.append(row_string)
        return "\n".join(board_rows)

    @staticmethod
    async def parse_from_file(filename: str):
        board = Board()
        try:
            contents = await asyncio.to_thread(Board._read_file_sync, filename)
            lines = contents.strip().splitlines()

            board_size = lines[0].strip()
            size_parts = board_size.split("x")
            if len(size_parts) != 2:
                raise ValueError("Invalid board size format, expected RxC like '3x3'")

            board.nr_rows = int(size_parts[0])
            board.nr_cols = int(size_parts[1])

            card_values = [line.strip() for line in lines[1:]]
            expected_nr_cards = board.nr_rows * board.nr_cols
            if len(card_values) != expected_nr_cards:
                raise ValueError(f"Invalid number of cards: expected {expected_nr_cards}, "
                                    f"got {len(card_values)}")

            board.cards = []
            i = 0
            for r in range(board.nr_rows):
                row_cards = []
                for c in range(board.nr_cols):
                    card_value = card_values[i]
                    card = Card(string_value=card_value)
                    row_cards.append(card)
                    i += 1
                board.cards.append(row_cards)

            return board

        except Exception as e:
            raise Exception(f"Error reading file '{filename}': {e}")

    @staticmethod
    def _read_file_sync(filename: str):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()