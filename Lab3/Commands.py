import time

from Lab3.Board import Board
import asyncio


async def clean_cards_last_round(player_id: str, board: Board):
    board.initialize_player_state(player_id)

    state = board.player_state[player_id]
    cards_to_clean = state["cards_last_turn"]
    matched_status = state["last_turn_matched"]

    if not cards_to_clean:
        return

    if matched_status:
        print(f"[{player_id}] Cleaning up matched pair: {cards_to_clean}")
        for row, column in cards_to_clean:
            card = board.get_card(row, column)

            if card.controller == player_id:
                card.removed = True
                card.face_up = False
                card.controller = None
                board.initialize_queue_for_card(row, column)
                queue = board.waiting_players_queue[(row, column)]

                if queue:
                    print(f"Clearing queue for removed card ({row},{column}).")
                    queue.clear()

    else:
        print(f"[{player_id}] Cleaning up mismatched cards: {cards_to_clean}")
        for row, column in cards_to_clean:
            card = board.get_card(row, column)
            if not card.removed and card.face_up and card.controller is None:
                card.face_up = False
                card.face_down = True
                card.matched = False
            elif card.controller == player_id and not card.removed:
                card.face_up = False
                card.face_down = True
                card.matched = False
                await release_control_and_update_queue(row, column, board)

    state["cards_last_turn"] = []
    state["last_turn_matched"] = False
    board.notify_watchers()


async def release_control_and_update_queue(row: int, col: int, board: Board):
    card = board.get_card(row, col)
    board.initialize_queue_for_card(row, col)
    queue = board.waiting_players_queue[(row, col)]

    if card.matched:
        card.controller = None
        if queue and len(queue) > 0:
            queue.clear()
            print(f"Cleared queue for matched card ({row},{col}).")
        return

    if queue and len(queue) > 0:
        next_player_id = queue.popleft()
        board.initialize_player_state(next_player_id)

        next_player_state = board.player_state[next_player_id]
        next_player_state["cards_this_round"].clear()

        card.controller = next_player_id
        next_player_state["cards_this_round"].append((row, col))

        print(f"[{next_player_id}] gained control of ({row},{col}) from queue.")
        board.notify_watchers()
    else:
        card.controller = None


async def flip(player_id: str, row: int, col: int, board: Board):
    async with board.board_lock:
        board.initialize_player_state(player_id)
        board.initialize_queue_for_card(row, col)

        state = board.player_state[player_id]
        current_cards = state["cards_this_round"]
        card = board.get_card(row, col)

        if card.matched:
            raise Exception("Card was already matched and is removed.")

        queue_players = board.waiting_players_queue[(row, col)]

        if len(current_cards) == 0:
            await clean_cards_last_round(player_id, board)

            if card.removed:
                raise Exception("Card is not on the board.")

            if card.matched:
                raise Exception("Card is already matched and will be removed.")

            if card.controller is not None:
                if player_id not in queue_players:
                    queue_players.append(player_id)
                    print(f"[{player_id}] was added to the queue for ({row},{col})")
                    board.notify_watchers()
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
            board.notify_watchers()
            return "First card selected."

        elif len(current_cards) == 1:
            first_card_position = current_cards[0]
            if first_card_position == (row, col):
                raise Exception("Cannot select the same card twice.")

            first_card = board.get_card(first_card_position[0], first_card_position[1])

            if card.removed:
                await release_control_and_update_queue(first_card_position[0], first_card_position[1], board)
                current_cards.clear()
                board.notify_watchers()
                raise Exception("Second card is not on the board. Lost control of first card.")

            if card.matched:
                await release_control_and_update_queue(first_card_position[0], first_card_position[1], board)
                current_cards.clear()
                board.notify_watchers()
                raise Exception("Second card is already matched. Lost control of first card.")

            if card.controller is not None:
                await release_control_and_update_queue(first_card_position[0], first_card_position[1], board)
                current_cards.clear()
                board.notify_watchers()
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
                board.notify_watchers()
                return "A match was found! User controls both cards."
            else:
                print(f"[{player_id}] No match.")
                await release_control_and_update_queue(first_card_position[0], first_card_position[1], board)
                state["last_turn_matched"] = False
                current_cards.clear()
                board.notify_watchers()
                return "No match found. Cards remain face up. Player no longer has control of first card."

        else:
            raise Exception("Invalid state: player has 2 cards in hand.")


async def look(board: Board, player_id: str):
    board.initialize_player_state(player_id)

    result = []
    for row in range(board.nr_rows):
        row_string = []
        for column in range(board.nr_cols):
            card = board.get_card(row, column)

            value: str
            if card.removed:
                value = "_"
            elif card.face_up:
                value = card.string_value
            else:
                value = "*"

            queue_state = "default"
            board.initialize_queue_for_card(row, column)
            queue = board.waiting_players_queue.get((row, column))

            if queue and len(queue) > 0:
                queue_state = "queued"

            cell_data = f"{value}:{queue_state}"
            row_string.append(cell_data)

        result.append(" ".join(row_string))

    return "\n".join(result)


async def map_card_value(value):
    if value == "🦄":
        return "☀️"
    elif value == "🌈":
        return "🍭"
    return value


async def watch(board: Board, player_id: str):
    print(f"[{player_id}] 👀 Watch starting, waiting for change...")
    await board.wait_for_change()
    print(f"[{player_id}] 🔔 Watch detected change, returning board")
    return await look(board, player_id)  # ✅ MUST have await here
