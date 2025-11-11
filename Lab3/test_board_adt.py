import unittest
import asyncio
from Lab3.Board import Board
from Lab3.Card import Card
import copy
import os
import tempfile


class TestCardADT(unittest.TestCase):
    def test_valid_states(self):
        """- Create a new card
        - Check it starts face-down
        - Flip it face up, assign controller, mark matched
        - Remove it
        - At each step: checkRep() should NOT throw
        """
        c = Card("A")
        c.checkRep()
        self.assertTrue(c.face_down)
        self.assertFalse(c.face_up)

        c.face_down = False
        c.face_up = True
        c.checkRep()

        c.controller = "P1"
        c.checkRep()

        c.matched = True
        c.checkRep()

        c.matched = False
        c.controller = None
        c.face_up = False
        c.face_down = False
        c.removed = True
        c.checkRep()


class TestBoardADT(unittest.IsolatedAsyncioTestCase):

    async def test_manual_construction_and_rep(self):
        """- Build a manual 2x2 board
            - Run checkRep() - should pass
            - Make one card face-up and controlled
            - checkRep() again - should still pass
            """
        b = Board()
        b.nr_rows = 2
        b.nr_cols = 2
        b.cards = [
            [Card("A"), Card("B")],
            [Card("A"), Card("B")]
        ]

        b.checkRep()

        b.cards[0][0].face_down = False
        b.cards[0][0].face_up = True
        b.cards[0][0].controller = "P1"

        b.checkRep()

    async def test_str_representation(self):
        """
        - Build board
        - Initial print should be "* *\n* *"
        - Flip a card - print should update
        - Remove a card - print shows "_"
        """
        b = Board()
        b.nr_rows = 2
        b.nr_cols = 2
        b.cards = [[Card("A"), Card("B")], [Card("A"), Card("B")]]

        self.assertEqual(str(b), "* *\n* *")

        b.cards[0][0].face_down = False
        b.cards[0][0].face_up = True
        self.assertEqual(str(b), "A *\n* *")

        b.cards[0][1].face_down = False
        b.cards[0][1].removed = True
        self.assertEqual(str(b), "A _\n* *")

    async def test_parseFromFile(self):
        """
        - Create temporary file 2x2 + values
        - parse_from_file() loads it
        - Check size and content
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            name = f.name
            f.write("2x2\nA\nB\nC\nD\n")

        board = await Board.parse_from_file(name)
        self.assertEqual(board.nr_rows, 2)
        self.assertEqual(board.nr_cols, 2)
        self.assertEqual(board.get_card(0, 0).string_value, "A")
        self.assertEqual(board.get_card(1, 1).string_value, "D")

        os.remove(name)

    async def test_parse_invalid_size(self):
        """
        - Write invalid header
        - parse_from_file() should raise
        """
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            name = f.name
            f.write("AX2\nA\nB\n")

        with self.assertRaises(Exception):
            await Board.parse_from_file(name)

        os.remove(name)

    async def test_rep_exposure(self):
        """
        - Deep copy the card matrix
        - Change copied card’s value
        - Original card should not change
        """
        b = Board()
        b.nr_rows = 1
        b.nr_cols = 2
        b.cards = [[Card("A"), Card("B")]]

        local = copy.deepcopy(b.cards)
        local[0][0].string_value = "X"

        self.assertEqual(b.cards[0][0].string_value, "A")
