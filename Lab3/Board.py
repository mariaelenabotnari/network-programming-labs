import asyncio
from collections import deque
from typing import List, Optional
from Lab3.Card import Card


class Board:

    def __init__(self) -> None:
        self._player_state: dict[str, dict] = {}
        self._nr_cols: int = 0
        self._nr_rows: int = 0
        self._cards: list[list['Card']] = []
        self._change_event = asyncio.Event()
        self._board_lock = asyncio.Lock()
        self._waiting_players_queue: dict[tuple[int, int], deque[str]] = {}

    def checkRep(self) -> None:
        """
        REQUIRES:
            - None

        MODIFIES:
            - None

        EFFECTS:
            - Asserts that:
                * nr_rows, nr_cols >= 0
                * cards is a list of nr_rows lists
                * each row has nr_cols items
                * each item is a Card
                * every card satisfies Card.checkRep()

            - If nr_rows == 0 or nr_cols == 0:
                cards must be empty

        THROWS:
            - AssertionError if any representation invariant is violated
        """
        assert self._nr_rows >= 0, "Number of rows must be non-negative"
        assert self._nr_cols >= 0, "Number of columns must be non-negative"
        assert isinstance(self._cards, list), "_cards must be a list"

        if self._nr_rows == 0 or self._nr_cols == 0:
            assert len(self._cards) == 0, "Empty board must have empty cards list"
            return

        assert len(self._cards) == self._nr_rows, "Row dimension mismatch"

        for r in range(self._nr_rows):
            row = self._cards[r]
            assert isinstance(row, list), "Each row in _cards must be a list"
            assert len(row) == self._nr_cols, f"Column dimension mismatch in row {r}"

            for c in range(self._nr_cols):
                card = self.get_card(r, c)
                assert isinstance(card, Card), f"Item at ({r},{c}) is not a Card"

                card.checkRep()


    @property
    def nr_cols(self) -> int:
        return self._nr_cols

    @nr_cols.setter
    def nr_cols(self, value: int):
        self._nr_cols = value

    @property
    def nr_rows(self) -> int:
        return self._nr_rows

    @nr_rows.setter
    def nr_rows(self, value: int):
        self._nr_rows = value

    @property
    def cards(self) -> List[List['Card']]:
        return self._cards

    @cards.setter
    def cards(self, value: List[List['Card']]):
        self._cards = value

    @property
    def player_state(self) -> dict:
        return self._player_state

    @property
    def waiting_players_queue(self) -> dict:
        return self._waiting_players_queue

    @property
    def change_event(self) -> asyncio.Event:
        return self._change_event

    @property
    def board_lock(self):
        return self._board_lock

    def get_card(self, row: int, col: int) -> Card:
        """
        REQUIRES:
            - 0 <= row < nr_rows
            - 0 <= col < nr_cols

        MODIFIES:
            - None

        EFFECTS:
            - Returns the Card at (row, col)

        RETURNS:
            - Card

        THROWS:
            - IndexError if row/col out of bounds
        """
        return self.cards[row][col]

    def __str__(self) -> str:
        """
        REQUIRES:
            - Board is in a valid state (checkRep holds)

        MODIFIES:
            - None

        EFFECTS:
            - Produces a textual representation of the board:
                  removed -> "_"
                  face-up -> card.string_value
                  face-down -> "*"
            - Rows separated by newline; cards separated by spaces

        RETURNS:
            - String representation of board

        THROWS:
            - None
        """
        board_rows = []
        for r in range(self.nr_rows):
            row_string = " ".join(str(self.cards[r][c]) for c in range(self.nr_cols))
            board_rows.append(row_string)
        return "\n".join(board_rows)

    def initialize_player_state(self, player_id: str) -> None:
        """
        REQUIRES:
            - player_id is a hashable identifier

        MODIFIES:
            - player_state

        EFFECTS:
            - If player_id not yet in player_state:
                inserts an entry
                    {
                       "cards_this_round": [],
                       "cards_last_turn": [],
                       "last_turn_matched": False
                    }
            - Otherwise no effect

        THROWS:
            - None
        """
        if player_id not in self.player_state:
            self.player_state[player_id] = {
                "cards_this_round": [],
                "cards_last_turn": [],
                "last_turn_matched": False
            }

    def initialize_queue_for_card(self, row, column) -> None:
        """
        REQUIRES:
            - (row, column) is a valid board position

        MODIFIES:
            - waiting_players_queue

        EFFECTS:
            - Ensures waiting_players_queue[(row, column)] exists,
              creating an empty queue if needed

        THROWS:
            - None
        """
        if (row, column) not in self.waiting_players_queue:
            self.waiting_players_queue[(row, column)] = deque()

    @staticmethod
    async def parse_from_file(filename: str) -> "Board":
        """
        REQUIRES:
            - filename refers to an existing readable file
            - file contents follow format:
                first line: "<R>x<C>"
                next R*C lines: card values

        MODIFIES:
            - None (creates and returns a new Board)

        EFFECTS:
            - Reads board size from first line
            - Constructs a Board of size R x C
            - Creates Card objects initialized face-down
            - Populates row-major order
            - Validates representation with checkRep()

        RETURNS:
            - A new valid Board instance

        THROWS:
            - ValueError if format is invalid (#rows/cols incorrect)
            - Exception on read problems or malformed structure
        """
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

            board.checkRep()

            return board

        except Exception as e:
            raise Exception(f"Error reading file '{filename}': {e}")

    @staticmethod
    def _read_file_sync(filename: str) -> str:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
