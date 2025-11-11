from typing import Optional

from Lab3.Board import Board


class Commands:
    def __init__(self, board: Board):
        self.board = board

    def _to_tuple(self, row: int, col: int) -> tuple[int, int]:
        return (row, col)

    def notify_watchers(self) -> None:
        self.board.change_event.set()

    async def wait_for_change(self) -> None:
        await self.board.change_event.wait()
        self.board.change_event.clear()

    def _player_is_waiting(self, player_id: str) -> bool:
        """
        REQUIRES:
            - player_id is a valid player identifier (string).
            - board.waiting_players_queue is properly initialized
              (i.e., a dict mapping (row, col) → deque of player_ids).

        MODIFIES:
            - None

        EFFECTS:
            - Checks whether the given player_id appears in the waiting queue
              of any card on the board.
            - Does not modify board state.

        RETURNS:
            - True  if the player is present in at least one queue.
            - False otherwise.

        THROWS:
            - None
        """
        for q in self.board.waiting_players_queue.values():
            if player_id in q:
                return True
        return False

    def _transfer_responsibility_to_current_controller(self, row: int, column: int, new_owner_id: str) -> None:
        """
        REQUIRES:
            - (row, col) is a valid board position.
            - new_owner_id is a valid player id existing in player_state.

        MODIFIES:
            - board.player_state

        EFFECTS:
            - Removes (row, col) from every other player's cards_last_turn list,
              leaving it only in new_owner_id’s responsibility scope.
            - Does not modify the card object itself.

        THROWS:
            - None
        """
        position = self._to_tuple(row, column)
        for other_id, other_state in self.board.player_state.items():
            if other_id == new_owner_id:
                continue
            if position in other_state.get("cards_last_turn", []):
                other_state["cards_last_turn"] = [p for p in other_state["cards_last_turn"] if p != position]
                print(f"[{new_owner_id}] Taking responsibility for {position} from {other_id}")

    def _record_last_turn_cards(self, player_id: str, a: tuple[int, int], b: Optional[tuple[int, int]], matched: bool) -> None:
        """
        REQUIRES:
            - player_id is in board.player_state
            - a and b (if provided) are valid (row, col) positions
            - Board is in valid state (checkRep holds)

        MODIFIES:
            - board.player_state[player_id]

        EFFECTS:
            - Sets player_state[player_id]["cards_last_turn"] to [a] if b is None,
              or [a, b] if b is not None.
            - Sets last_turn_matched to the given matched value.
            - Overwrites any previous last-turn record.

        THROWS:
            - None
        """
        state = self.board.player_state[player_id]
        if b is None:
            state["cards_last_turn"] = [a]
        else:
            state["cards_last_turn"] = [a, b]
        state["last_turn_matched"] = matched

    async def clean_cards_last_round(self, player_id: str) -> None:
        """
        REQUIRES:
            - player_id is a valid player.
            - Board is in a valid state (checkRep holds).

        MODIFIES:
            - Card states of the relevant previous-turn cards.
            - board.player_state
            - board.waiting_players_queue
            - Raises change notifications

        EFFECTS:
            - If the player matched last turn, each matching card they still control
              becomes removed, face-down, and uncontrolled, and queues for those cards are cleared.
            - If the player mismatched, those cards (if face-up and uncontrolled)
              are turned face-down.
            - cards_last_turn and last_turn_matched are cleared.

        THROWS:
            - None
        """
        self.board.initialize_player_state(player_id)
        state = self.board.player_state[player_id]
        cards_to_clean = state["cards_last_turn"]
        matched_status = state["last_turn_matched"]

        if not cards_to_clean:
            return

        if matched_status:
            # 3-A: remove matched pair the player still controls
            print(f"[{player_id}] Cleaning up matched pair: {cards_to_clean}")
            for row, column in cards_to_clean:
                card = self.board.get_card(row, column)
                if card.controller == player_id:
                    card.removed = True
                    card.face_up = False
                    card.controller = None

                    # clear any queue for a removed card
                    self.board.initialize_queue_for_card(row, column)
                    q = self.board.waiting_players_queue[(row, column)]
                    if q:
                        q.clear()
                        print(f"Clearing queue for removed card ({row},{column}).")
        else:
            # 3-B: flip face-down any last-turn cards the player previously controlled
            # that are still on the board, face-up, and uncontrolled
            print(f"[{player_id}] Cleaning up mismatched cards: {cards_to_clean}")
            for row, column in cards_to_clean:
                card = self.board.get_card(row, column)
                if not card.removed and card.face_up and card.controller is None:
                    card.face_up = False
                    card.face_down = True
                    card.matched = False

        state["cards_last_turn"] = []
        state["last_turn_matched"] = False
        self.notify_watchers()

    async def release_control_and_update_queue(self, row: int, col: int) -> None:
        """
        REQUIRES:
            - (row, col) indexes are in range.
            - Board is in valid state.

        MODIFIES:
            - card.controller
            - board.waiting_players_queue
            - next player’s cards_this_round

        EFFECTS:
            - If card is matched, controller is set to None and queue cleared.
            - Otherwise, if queue is non-empty, next queued player becomes controller
              and their cards_this_round becomes [(row,col)].
            - If queue empty, controller becomes None.

        THROWS:
            - None
        """
        card = self.board.get_card(row, col)
        self.board.initialize_queue_for_card(row, col)
        queue = self.board.waiting_players_queue[(row, col)]

        if card.matched:
            # matched cards will be removed by 3-A later; keep uncontrolled
            card.controller = None
            if queue:
                queue.clear()
                print(f"Cleared queue for matched card ({row},{col}).")
            return

        if queue:
            # Give control to next in queue immediately (1-D)
            next_player_id = queue.popleft()
            self.board.initialize_player_state(next_player_id)
            next_state = self.board.player_state[next_player_id]

            card.controller = next_player_id

            self._transfer_responsibility_to_current_controller(row, col, next_player_id)

            next_state["cards_this_round"].clear()
            next_state["cards_this_round"].append(self._to_tuple(row, col))

            print(f"[{next_player_id}] gained control of ({row},{col}) from queue.")
            self.notify_watchers()
        else:
            card.controller = None

    async def flip(self, player_id: str, row: int, col: int) -> Optional[str]:
        """
        REQUIRES:
            - player_id is a valid identifier
            - (row, col) is within board bounds
            - Board is in a legal rep state

        MODIFIES:
            - Card states (face_up/down, matched, controller)
            - board.player_state
            - board.waiting_players_queue

        EFFECTS:
            - Implements Memory Scramble rules 1, 2, and 3.
            - If the player begins a turn (no cards_this_round), their previous-turn
              cleanup (3-A/3-B) is done first.
            - Behavior follows:
                1-A: flipping removed → failure
                1-B: flip face-down → face-up & control
                1-C: take control if face-up & uncontrolled
                1-D: queue if another player controls

                2-A: second flip removed → lose first; failure
                2-B: second flip controlled → lose first; failure
                2-C: flip second face-down → face-up & control
                2-D: match → both marked matched
                2-E: mismatch → control released, face-up

            - On match/mismatch, stores last_turn cards and clears cards_this_round.
            - Notifies watchers when a visible change occurs.

        RETURNS:
            - Success message, or raises exception

        THROWS:
            - Exception (with reason string) on illegal moves per rules.
        """
        async with self.board.board_lock:
            try:
                if self._player_is_waiting(player_id):
                    raise Exception(
                        "You are in a queue and must wait your turn before flipping another card."
                    )

                self.board.initialize_player_state(player_id)
                self.board.initialize_queue_for_card(row, col)

                state = self.board.player_state[player_id]
                current_cards = state["cards_this_round"]
                card = self.board.get_card(row, col)
                queue_players = self.board.waiting_players_queue[(row, col)]
                position = self._to_tuple(row, col)

                # ======== FIRST CARD ========
                if len(current_cards) == 0:
                    # 3-A/3-B before starting a new first-card attempt
                    await self.clean_cards_last_round(player_id)

                    # 1-A / already removed or invalid
                    if card.removed:
                        raise Exception("Card is not on the board.")
                    # Not allowed to pick a card already matched (will be removed)
                    if card.matched:
                        raise Exception("Card is already matched and will be removed.")

                    # 1-D: controlled by another player -> join queue; do not wait
                    if card.controller is not None and card.controller != player_id:
                        if player_id not in queue_players:
                            queue_players.append(player_id)
                            print(f"[{player_id}] was added to the queue for {position}")
                            self.notify_watchers()
                            raise Exception("Card is controlled. You are now in the queue.")
                        else:
                            raise Exception("You are already in the queue for this card.")

                    # 1-B/1-C
                    if card.face_down:
                        # 1-B: flip up and control it
                        card.face_up = True
                        card.face_down = False
                        card.controller = player_id
                        print(f"[{player_id}] Flipped first card.")
                    else:
                        # card.face_up and not controlled by another -> 1-C: take control
                        card.controller = player_id
                        print(f"[{player_id}] Took control of face-up card.")

                    # transfer responsibility for this card to current player
                    self._transfer_responsibility_to_current_controller(row, col, player_id)

                    current_cards.append(position)
                    self.notify_watchers()
                    return "First card selected."

                # ======== SECOND CARD ========
                elif len(current_cards) == 1:
                    first_pos = current_cards[0]
                    if first_pos == position:
                        # selecting same card twice is an immediate fail
                        print(f"[{player_id}] Failed by selecting same card twice.")
                        await self.release_control_and_update_queue(first_pos[0], first_pos[1])
                        self._record_last_turn_cards(player_id, first_pos, None, matched=False)
                        current_cards.clear()
                        raise Exception("Cannot select the same card twice.")

                    first_card = self.board.get_card(first_pos[0], first_pos[1])

                    # 2-A: second card gone
                    if card.removed:
                        await self.release_control_and_update_queue(first_pos[0], first_pos[1])
                        self._record_last_turn_cards(player_id, first_pos, None, matched=False)
                        current_cards.clear()
                        self.notify_watchers()
                        raise Exception("Second card is not on the board. Lost control of first card.")

                    # 2-B: second card controlled by anyone
                    if card.controller is not None:
                        await self.release_control_and_update_queue(first_pos[0], first_pos[1])
                        self._record_last_turn_cards(player_id, first_pos, None, matched=False)
                        current_cards.clear()
                        self.notify_watchers()
                        raise Exception("Second card is controlled. Lost control of first card.")

                    # 2-C / 2-D / 2-E
                    if card.face_down:
                        # Flip up and control
                        card.face_up = True
                        card.face_down = False
                        card.controller = player_id
                        print(f"[{player_id}] Flipped second card.")
                    else:
                        # face up & uncontrolled -> take control
                        card.controller = player_id
                        print(f"[{player_id}] Took control of second face-up card.")

                    # transfer responsibility for the second card as well
                    self._transfer_responsibility_to_current_controller(row, col, player_id)

                    if first_card.string_value == card.string_value:
                        # 2-D match: keep control now; 3-A will remove at next first-card attempt
                        print(f"[{player_id}] Match found!")
                        first_card.matched = True
                        card.matched = True
                        self._record_last_turn_cards(player_id, first_pos, position, matched=True)
                        current_cards.clear()
                        self.notify_watchers()
                        return "A match was found! User controls both cards."
                    else:
                        # 2-E mismatch
                        print(f"[{player_id}] No match.")
                        await self.release_control_and_update_queue(first_pos[0], first_pos[1])
                        await self.release_control_and_update_queue(row, col)
                        self._record_last_turn_cards(player_id, first_pos, position, matched=False)
                        current_cards.clear()
                        self.notify_watchers()
                        print(f"First and second card controller: {first_card.controller} {card.controller}")
                        return "No match found. Cards remain face up. Player no longer has control of both cards."

                else:
                    raise Exception("Invalid state: player has 2 cards in hand.")

            finally:
                self.board.checkRep()

    async def look(self, player_id: str) -> str:
        """
        REQUIRES:
            - player_id must be a valid identifier

        MODIFIES:
            - Initializes board.player_state[player_id] if missing.

        EFFECTS:
            - Returns string representation of each card:
                <value>:<queue_state>[:my]
            - Does NOT block.
            - Does NOT change card states.

        RETURNS:
            - A newline-separated board representation.

        THROWS:
            - None
        """
        self.board.initialize_player_state(player_id)

        result = []
        for row in range(self.board.nr_rows):
            row_string = []
            for column in range(self.board.nr_cols):
                card = self.board.get_card(row, column)

                if card.removed:
                    value = "_"
                elif card.face_up:
                    value = card.string_value
                else:
                    value = "*"

                self.board.initialize_queue_for_card(row, column)
                queue = self.board.waiting_players_queue.get((row, column))
                queue_state = "queued" if (queue and len(queue) > 0) else "default"
                control_flag = "my" if (card.controller == player_id) else ""

                cell_data = f"{value}:{queue_state}" + (":my" if control_flag else "")
                row_string.append(cell_data)

            result.append(" ".join(row_string))

        return "\n".join(result)

    async def reset_board(self) -> None:
        """
        REQUIRES:
            - Board must be in any valid state.

        MODIFIES:
            - All cards
            - player_state
            - waiting_players_queue

        EFFECTS:
            - Restores board to initial fresh state:
                all cards face-down, not removed, not matched, no controller.
            - Clears all player state and queues.
            - Notifies watchers.

        THROWS:
            - None
        """
        print("Resetting the board...")
        async with self.board.board_lock:
            for r in range(self.board.nr_rows):
                for c in range(self.board.nr_cols):
                    card = self.board.get_card(r, c)
                    card.face_down = True
                    card.face_up = False
                    card.removed = False
                    card.controller = None
                    card.matched = False

            self.board.player_state.clear()
            self.board.waiting_players_queue.clear()
            print("Board has been reset.")
        self.notify_watchers()

    async def replace_card_value(self, old_value: str, new_value: str) -> None:
        """
        REQUIRES:
            - old_value != "", new_value != ""
            - old_value appears on board
            - new_value does NOT exist on board
            - old_value != new_value

        MODIFIES:
            - string_value of matching cards

        EFFECTS:
            - All non-removed cards with string_value == old_value
              are updated to new_value.
            - Board remains consistent.
            - Notifies watchers.

        THROWS:
            - ValueError if invalid input or board constraint violated
        """
        if not old_value or not new_value:
            raise ValueError("Both 'old' and 'new' values are required.")
        if old_value == new_value:
            raise ValueError("Old and new cards cannot be the same.")

        async with self.board.board_lock:
            print(f"Attempting to replace '{old_value}' with '{new_value}'")
            unique_values = set()
            for row in range(self.board.nr_rows):
                for column in range(self.board.nr_cols):
                    if not self.board.cards[row][column].removed:
                        unique_values.add(self.board.cards[row][column].string_value)

            if old_value not in unique_values:
                raise ValueError(f"Card value '{old_value}' not found on the board.")
            if new_value in unique_values:
                raise ValueError(f"Card value '{new_value}' is already on the board. Cards must be unique.")

            replaced_count = 0
            for row in range(self.board.nr_rows):
                for column in range(self.board.nr_cols):
                    card = self.board.get_card(row, column)
                    if not card.removed and card.string_value == old_value:
                        card.string_value = new_value
                        replaced_count += 1

            print(f"Replaced {replaced_count} instances of '{old_value}'.")
            print("Replacement complete.")
        self.notify_watchers()
