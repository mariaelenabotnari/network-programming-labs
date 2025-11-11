import unittest
import asyncio
from Lab3.Board import Board
from Lab3.Card import Card
from Lab3.CommandsImpl import Commands


class TestConcurrency(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.board = Board()
        self.board.nr_rows = 1
        self.board.nr_cols = 2
        self.board.cards = [[Card("A"), Card("A")]]
        self.cmds = Commands(self.board)

    async def test_1D_enqueues(self):
        """
        - P1 flips card - takes control
        - P2 tries - must be queued
        - Check P2 is in queue
        - checkRep() - board still valid
        """
        await self.cmds.flip("P1", 0, 0)

        with self.assertRaisesRegex(Exception, "queue"):
            await self.cmds.flip("P2", 0, 0)

        self.assertIn("P2", self.board.waiting_players_queue[(0, 0)])
        self.board.checkRep()

    async def test_queue_resolution_on_mismatch(self):
        """
        - P1 controls first card
        - P2 tries - gets queued
        - Change second card to cause mismatch
        - P1 flips mismatch - P1 loses control, P2 should now control first card
        """
        await self.cmds.flip("P1", 0, 0)

        try:
            await self.cmds.flip("P2", 0, 0)
        except:
            pass

        self.board.cards[0][1].string_value = "B"

        await self.cmds.flip("P1", 0, 1)

        self.assertEqual(self.board.cards[0][0].controller, "P2")
        self.assertNotIn("P2", self.board.waiting_players_queue[(0, 0)])
        self.board.checkRep()

    async def test_FIFO_queue_order(self):
        """
        - P1 controls card
        - P2 - queued
        - P3 - queued
        - P4 - queued

        Check queue = [P2, P3, P4] (FIFO)

        - Force mismatch
        - P2 must gain control

        - Force another mismatch
        - P3 gains control next
        """
        await self.cmds.flip("P1", 0, 0)

        # Queue P2, P3, P4
        for p in ["P2", "P3", "P4"]:
            try:
                await self.cmds.flip(p, 0, 0)
            except:
                pass

        self.assertEqual(list(self.board.waiting_players_queue[(0, 0)]),
                         ["P2", "P3", "P4"])

        self.board.cards[0][1].string_value = "B"

        await self.cmds.flip("P1", 0, 1)

        self.assertEqual(self.board.get_card(0, 0).controller, "P2")

        self.board.cards[0][1].controller = None
        self.board.cards[0][1].face_up = False
        self.board.cards[0][1].string_value = "C"

        await self.cmds.flip("P2", 0, 1)

        self.assertEqual(self.board.get_card(0, 0).controller, "P3")

        self.board.checkRep()


if __name__ == '__main__':
    unittest.main()
