import unittest
import asyncio
from Lab3.Board import Board
from Lab3.Card import Card
from Lab3.CommandsImpl import Commands  # Assuming your inline Commands is saved here


class TestGameRules(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        """Set up a 2x2 Board [A, B] / [A, B] for each test."""
        self.board = Board()
        self.board.nr_rows = 2
        self.board.nr_cols = 2
        self.board.cards = [
            [Card("A"), Card("B")],
            [Card("A"), Card("B")]
        ]
        self.cmds = Commands(self.board)

    async def test_1A_flip_removed_fails(self):
        """
        Rule 1-A:
        If a player tries to flip a card that is already removed,
        the action must fail and raise an exception.
        """
        self.board.cards[0][0].face_down = False
        self.board.cards[0][0].removed = True

        with self.assertRaisesRegex(Exception, "Card is not on the board"):
            await self.cmds.flip("P1", 0, 0)

    async def test_1B_flip_facedown(self):
        """
        Rule 1-B:
        If a face-down card is flipped as the first card,
        it becomes face-up and the player becomes its controller.
        """
        msg = await self.cmds.flip("P1", 0, 0)
        self.assertEqual(msg, "First card selected.")

        card = self.board.get_card(0, 0)
        self.assertTrue(card.face_up)
        self.assertEqual(card.controller, "P1")
        self.board.checkRep()

    async def test_1C_flip_faceup_uncontrolled(self):
        """
        Rule 1-C:
        If a card is face-up and uncontrolled,
        flipping it gives control to the player.
        """
        self.board.cards[0][0].face_down = False
        self.board.cards[0][0].face_up = True
        self.board.cards[0][0].controller = None

        await self.cmds.flip("P1", 0, 0)
        self.assertEqual(self.board.cards[0][0].controller, "P1")

    async def test_2A_second_flip_removed_fails(self):
        """
        Rule 2-A:
        If the player flips a removed card as their second card,
        the turn fails and the player loses control of the first card.
        """
        await self.cmds.flip("P1", 0, 0)

        self.board.cards[0][1].face_down = False
        self.board.cards[0][1].removed = True

        with self.assertRaisesRegex(Exception, "Second card is not on the board"):
            await self.cmds.flip("P1", 0, 1)

        self.assertIsNone(self.board.cards[0][0].controller)
        self.assertTrue(self.board.cards[0][0].face_up)

    async def test_2B_second_flip_self_controlled_fails(self):
        """
        Rule 2-B:
        If the second flip selects the same controlled card again,
        the move fails and the first card’s control is relinquished.
        """
        await self.cmds.flip("P1", 0, 0)

        with self.assertRaisesRegex(Exception, "Cannot select the same card twice"):
            await self.cmds.flip("P1", 0, 0)

        self.assertIsNone(self.board.cards[0][0].controller)

    async def test_2D_match_success(self):
        """
        Rule 2-D:
        When the second card matches the first,
        both cards become matched and stay controlled by the player.
        last_turn records both positions.
        """
        await self.cmds.flip("P1", 0, 0)  # 'A'
        msg = await self.cmds.flip("P1", 1, 0)  # 'A' at (1,0)

        self.assertIn("match was found", msg)

        c1 = self.board.get_card(0, 0)
        c2 = self.board.get_card(1, 0)
        self.assertTrue(c1.matched and c2.matched)
        self.assertEqual(c1.controller, "P1")
        self.assertEqual(c2.controller, "P1")

    async def test_2E_mismatch(self):
        """
        Rule 2-E:
        If the second card does not match the first,
        both are left face-up but become uncontrolled (no controller).
        """
        await self.cmds.flip("P1", 0, 0)  # 'A'
        msg = await self.cmds.flip("P1", 0, 1)  # 'B'

        self.assertIn("No match found", msg)
        c1 = self.board.get_card(0, 0)
        c2 = self.board.get_card(0, 1)

        # Remain face up
        self.assertTrue(c1.face_up and c2.face_up)
        # Relinquished control
        self.assertIsNone(c1.controller)
        self.assertIsNone(c2.controller)
        # Not matched
        self.assertFalse(c1.matched or c2.matched)

    async def test_3A_cleanup_match(self):
        """
        Rule 3-A:
        After a match, the cards are removed at the start of the next turn
        (for example, next first-card flip).
        """
        await self.cmds.flip("P1", 0, 0)
        await self.cmds.flip("P1", 1, 0)

        # Cards still on board, just matched
        self.assertFalse(self.board.cards[0][0].removed)

        # Start NEXT turn (flip a different card)
        await self.cmds.flip("P1", 0, 1)

        # Previous match should now be REMOVED
        self.assertTrue(self.board.cards[0][0].removed)
        self.assertTrue(self.board.cards[1][0].removed)
        self.assertIsNone(self.board.cards[0][0].controller)

    async def test_3B_cleanup_mismatch(self):
        """
        Rule 3-B:
        After a mismatch, the unmatched cards are turned face-down
        at the start of the next turn (i.e., next first-card flip).
        """
        await self.cmds.flip("P1", 0, 0)  # 'A'
        await self.cmds.flip("P1", 0, 1)  # 'B' - mismatch, both relinquished but face up

        self.assertTrue(self.board.cards[0][0].face_up)

        # Start NEXT turn
        await self.cmds.flip("P1", 1, 0)

        # Previous mismatched cards should now be face DOWN
        self.assertTrue(self.board.cards[0][0].face_down)
        self.assertTrue(self.board.cards[0][1].face_down)
        self.assertFalse(self.board.cards[0][0].face_up)


if __name__ == '__main__':
    unittest.main()