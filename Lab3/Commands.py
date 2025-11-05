import time

from Lab3.Board import Board
import asyncio


async def flip(player_id: str, row: int, col: int, board: Board):
    if player_id not in board.player_state:
        board.player_state[player_id] = {"controlled_cards": [], "matched_last_turn": False}

    card = board.get_card(row, col)
    controlled = board.player_state[player_id]["controlled_cards"]

    if card.removed:
        print("Cannot flip removed card.")
        raise Exception("Cannot flip removed card.")

    if card.face_up:
        print("Card is already up.")
        raise Exception("Card is already up.")

    if len(controlled) >= 2:
        print("Two cards are already up.")
        raise Exception("Two cards are already up.")

    card.face_up = True
    card.face_down = False

    board.notify_watchers()

    if len(controlled) == 0:
        controlled.append((row, col))
        return False

    if len(controlled) == 1:
        if controlled[0] == (row, col):
            raise Exception("Cannot flip the same card twice.")
        controlled.append((row, col))
        return True

    return False


async def check_matching_cards(player_id: str, board: Board):

    controlled = board.player_state[player_id]["controlled_cards"]

    if len(controlled) != 2:
        return

    first_card_row, first_card_column = controlled[0]
    second_card_row, second_card_column = controlled[1]

    first_card = board.get_card(first_card_row, first_card_column)
    second_card = board.get_card(second_card_row, second_card_column)

    if first_card.string_value == second_card.string_value:
        print("Match found!")
        first_card.removed = True
        second_card.removed = True

    else:
        print("No match.")
        first_card.face_up = False
        first_card.face_down = True
        second_card.face_up = False
        second_card.face_down = True

    controlled.clear()
    board.notify_watchers()


async def look(board: Board, player_id: str):
    if player_id not in board.player_state:
        board.player_state[player_id] = {"controlled_cards": [], "matches_last_turn": False}

    visible_positions_set = set(board.player_state[player_id]["controlled_cards"])

    result = []
    for row in range(board.nr_rows):
        row_string = []
        for column in range(board.nr_cols):
            card = board.get_card(row, column)
            if card.removed:
                row_string.append("_")
            elif (row, column) in visible_positions_set or card.face_up:
                row_string.append(card.string_value)
            else:
                row_string.append("*")
        result.append(" ".join(row_string))

    return "\n".join(result)


async def map_card_value(value):
    time.sleep(0.1)
    if value == "🦄":
        return "☀️"
    elif value == "🌈":
        return "🍭"
    return value


async def watch(board: Board, player_id: str):
    await board.wait_for_change()
    return look(board, player_id)
