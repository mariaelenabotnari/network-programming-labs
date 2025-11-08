import time

from Lab3.Board import Board
import asyncio


async def flip(player_id: str, row: int, col: int, board: Board):
    return await board.flip(player_id, row, col)


async def look(board: Board, player_id: str):
    return await board.look(player_id)


async def map_card_value(board: Board, value):
    await board.map_card_value(value)


async def apply_map_command(board: Board, transformer_function):
    await board.apply_map(transformer_function)


async def watch(board: Board, player_id: str):
    return await board.watch(player_id)
