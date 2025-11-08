import asyncio
from collections import deque
from typing import List, Optional, Callable, Awaitable


class Card:
    def __init__(self, string_value: str, face_down: bool = True,
                 face_up: bool = False, removed: bool = False, player_id: Optional[str] = None):
        self.string_value = string_value
        self.face_down = face_down
        self.face_up = face_up
        self.removed = removed
        self.player_id = player_id
        self.controller: Optional[str] = None
        self.matched: bool = False

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
        self.change_event = asyncio.Event()
        self.board_lock = asyncio.Lock()
        self.waiting_players_queue = {}

    def notify_watchers(self):
        self.change_event.set()

    async def wait_for_change(self):
        await self.change_event.wait()
        self.change_event.clear()

    async def watch(self, player_id: str):
        await self.wait_for_change()
        return await self.look(player_id)

    def get_card(self, row: int, col: int):
        return self.cards[row][col]

    def __str__(self):
        board_rows = []
        for r in range(self.nr_rows):
            row_string = " ".join(str(self.cards[r][c]) for c in range(self.nr_cols))
            board_rows.append(row_string)
        return "\n".join(board_rows)

    def initialize_player_state(self, player_id: str):
        if player_id not in self.player_state:
            self.player_state[player_id] = {
                "cards_this_round": [],
                "cards_last_turn": [],
                "last_turn_matched": False
            }

    def initialize_queue_for_card(self, row, column):
        if (row, column) not in self.waiting_players_queue:
            self.waiting_players_queue[(row, column)] = deque()

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

    async def clean_cards_last_round(self, player_id: str):
        self.initialize_player_state(player_id)

        state = self.player_state[player_id]
        cards_to_clean = state["cards_last_turn"]
        matched_status = state["last_turn_matched"]

        if not cards_to_clean:
            return

        if matched_status:
            print(f"[{player_id}] Cleaning up matched pair: {cards_to_clean}")
            for row, column in cards_to_clean:
                card = self.get_card(row, column)

                if card.controller == player_id:
                    card.removed = True
                    card.face_up = False
                    card.controller = None
                    self.initialize_queue_for_card(row, column)
                    queue = self.waiting_players_queue[(row, column)]

                    if queue:
                        print(f"Clearing queue for removed card ({row},{column}).")
                        queue.clear()

        else:
            print(f"[{player_id}] Cleaning up mismatched cards: {cards_to_clean}")
            for row, column in cards_to_clean:
                card = self.get_card(row, column)
                if not card.removed and card.face_up and card.controller is None:
                    card.face_up = False
                    card.face_down = True
                    card.matched = False
                elif card.controller == player_id and not card.removed:
                    card.face_up = False
                    card.face_down = True
                    card.matched = False
                    await self.release_control_and_update_queue(row, column)

        state["cards_last_turn"] = []
        state["last_turn_matched"] = False
        self.notify_watchers()

    async def release_control_and_update_queue(self, row: int, col: int):
        card = self.get_card(row, col)
        self.initialize_queue_for_card(row, col)
        queue = self.waiting_players_queue[(row, col)]

        if card.matched:
            card.controller = None
            if queue and len(queue) > 0:
                queue.clear()
                print(f"Cleared queue for matched card ({row},{col}).")
            return

        if queue and len(queue) > 0:
            next_player_id = queue.popleft()
            self.initialize_player_state(next_player_id)

            next_player_state = self.player_state[next_player_id]
            next_player_state["cards_this_round"].clear()

            card.controller = next_player_id
            next_player_state["cards_this_round"].append((row, col))

            print(f"[{next_player_id}] gained control of ({row},{col}) from queue.")
            self.notify_watchers()
        else:
            card.controller = None

    async def flip(self, player_id: str, row: int, col: int):
        async with self.board_lock:
            self.initialize_player_state(player_id)
            self.initialize_queue_for_card(row, col)

            state = self.player_state[player_id]
            current_cards = state["cards_this_round"]
            card = self.get_card(row, col)

            queue_players = self.waiting_players_queue[(row, col)]

            if len(current_cards) == 0:
                await self.clean_cards_last_round(player_id)

                if card.removed:
                    raise Exception("Card is not on the board.")

                if card.matched:
                    raise Exception("Card is already matched and will be removed.")

                if card.controller is not None:
                    if player_id not in queue_players:
                        queue_players.append(player_id)
                        print(f"[{player_id}] was added to the queue for ({row},{col})")
                        self.notify_watchers()
                        raise Exception("Card is controlled. You are now in the queue.")
                    else:
                        raise Exception("You are already in the queue for this card.")

                if card.face_down:
                    card.face_up = True
                    card.face_down = False
                    print(f"[{player_id}] Flipped first card.")
                elif card.face_up and card.controller is None:
                    print(f"[{player_id}] Took control of face-up card.")

                card.controller = player_id
                current_cards.append((row, col))
                self.notify_watchers()
                return "First card selected."

            elif len(current_cards) == 1:
                first_card_position = current_cards[0]
                first_card = self.get_card(first_card_position[0], first_card_position[1])

                if first_card_position == (row, col):
                    print(f"[{player_id}] Failed by selecting same card twice.")
                    await self.release_control_and_update_queue(first_card_position[0], first_card_position[1])
                    state["cards_last_turn"] = [first_card_position]
                    state["last_turn_matched"] = False
                    current_cards.clear()

                    raise Exception("Cannot select the same card twice.")

                first_card = self.get_card(first_card_position[0], first_card_position[1])

                if card.removed:
                    await self.release_control_and_update_queue(first_card_position[0], first_card_position[1])
                    state["cards_last_turn"] = [first_card_position]
                    state["last_turn_matched"] = False
                    current_cards.clear()
                    self.notify_watchers()
                    raise Exception("Second card is not on the board. Lost control of first card.")

                if card.matched:
                    await self.release_control_and_update_queue(first_card_position[0], first_card_position[1])
                    state["cards_last_turn"] = [first_card_position]
                    state["last_turn_matched"] = False
                    current_cards.clear()
                    self.notify_watchers()
                    raise Exception("Second card is already matched. Lost control of first card.")

                if card.controller is not None:
                    await self.release_control_and_update_queue(first_card_position[0], first_card_position[1])
                    state["cards_last_turn"] = [first_card_position]
                    state["last_turn_matched"] = False
                    current_cards.clear()
                    self.notify_watchers()
                    raise Exception("Second card is controlled. Lost control of first card.")

                if card.face_down:
                    card.face_up = True
                    card.face_down = False
                    print(f"[{player_id}] Flipped second card.")

                state["cards_last_turn"] = [first_card_position, (row, col)]

                if first_card.string_value == card.string_value:
                    print(f"[{player_id}] Match found!")
                    card.controller = player_id
                    state["last_turn_matched"] = True
                    first_card.matched = True
                    card.matched = True
                    current_cards.clear()
                    self.notify_watchers()
                    return "A match was found! User controls both cards."
                else:
                    print(f"[{player_id}] No match.")
                    await self.release_control_and_update_queue(first_card_position[0], first_card_position[1])
                    state["last_turn_matched"] = False
                    current_cards.clear()
                    self.notify_watchers()
                    return "No match found. Cards remain face up. Player no longer has control of first card."

            else:
                raise Exception("Invalid state: player has 2 cards in hand.")

    async def look(self, player_id: str):
        self.initialize_player_state(player_id)

        result = []
        for row in range(self.nr_rows):
            row_string = []
            for column in range(self.nr_cols):
                card = self.get_card(row, column)

                value: str
                if card.removed:
                    value = "_"
                elif card.face_up:
                    value = card.string_value
                else:
                    value = "*"

                queue_state = "default"
                self.initialize_queue_for_card(row, column)
                queue = self.waiting_players_queue.get((row, column))

                if queue and len(queue) > 0:
                    queue_state = "queued"

                cell_data = f"{value}:{queue_state}"
                row_string.append(cell_data)

            result.append(" ".join(row_string))

        return "\n".join(result)

    async def apply_map(self, transformer_function: Callable[[str], Awaitable[str]]):
        print("Starting map transformation")
        unique_values = set()
        for row in range(self.nr_rows):
            for column in range(self.nr_cols):
                if not self.cards[row][column].removed:
                    unique_values.add(self.cards[row][column].string_value)
        if not unique_values:
            print("No values to map")
            return

        print(f"Unique values to map: {unique_values}")

        tasks = []
        for val in unique_values:
            tasks.append(transformer_function(val))

        try:
            new_values = await asyncio.gather(*tasks)
            mapping = dict(zip(unique_values, new_values))
            print(f"Created mapping: {mapping}")
        except Exception as e:
            print(f"Error during mapping transformation: {e}")
            return

        async with self.board_lock:
            print("Applying map to board")
            for row in range(self.nr_rows):
                for column in range(self.nr_cols):
                    card = self.get_card(row, column)
                    if not card.removed and card.string_value in mapping:
                        card.string_value = mapping[card.string_value]

        self.notify_watchers()
        print("Map transformation done.")

    async def map_card_value(self, value):
        if value == "🦄":
            return "☀️"
        elif value == "🌈":
            return "🍭"
        return value
