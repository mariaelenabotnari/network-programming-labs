import asyncio
import time

from Lab3.Board import Board


def flip(player_id: str, row: int, col: int, board: Board):
    if player_id not in board.player_state:
        board.player_state[player_id] = {"controlled_cards": [], "matched_last_turn": False}

    card = board.get_card(row, col)
    controlled = board.player_state[player_id]["controlled_cards"]

    if card.removed:
        print("Cannot flip removed card.")
        return

    if card.face_up:
        print("Card is already up.")
        return

    if len(controlled) == 0:
        card.face_up = True
        card.face_down = False
        controlled.append((row, col))
        return

    if len(controlled) == 1:
        card.face_up = True
        card.face_down = False
        controlled.append((row, col))

        first_card_row, first_card_col = controlled[0]
        first_card = board.get_card(first_card_row, first_card_col)

        if first_card.string_value == card.string_value:
            print("Match found!")
            first_card.removed = True
            card.removed = True
        else:
            print("No match.")
            time.sleep(1)
            first_card.face_up = False
            first_card.face_down = False
            card.face_up = False
            card.face_down = True

        controlled.clear()


def look(board: Board, player_id: str):
    if player_id not in board.player_state:
        board.player_state[player_id] = {"controlled_cards": [], "matches_last_turn":False}

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


def map():
    pass


def watch():
    pass