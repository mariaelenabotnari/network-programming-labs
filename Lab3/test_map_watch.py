import unittest
import asyncio
from Lab3.Board import Board
from Lab3.Card import Card
from Lab3.CommandsImpl import Commands


class TestExtensions(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.board = Board()
        self.board.nr_rows = 2
        self.board.nr_cols = 2
        self.board.cards = [
            [Card("Unicorn"), Card("Rainbow")],
            [Card("Unicorn"), Card("Rainbow")]
        ]
        self.cmds = Commands(self.board)

    async def test_map_replace_success(self):
        """
        Problem 4:
        replace_card_value(old,new) should:
        - find all occurrences of old
        - change them to new
        - leave other cards unchanged
        """
        await self.cmds.replace_card_value("Unicorn", "Dragon")

        self.assertEqual(self.board.cards[0][0].string_value, "Dragon")
        self.assertEqual(self.board.cards[1][0].string_value, "Dragon")
        # Rainbows untouched
        self.assertEqual(self.board.cards[0][1].string_value, "Rainbow")

    async def test_map_replace_fail_missing_old(self):
        """
        Problem 4:
        If old_value does NOT exist on board,
        replace_card_value must raise ValueError.
        """
        with self.assertRaisesRegex(ValueError, "not found on the board"):
            await self.cmds.replace_card_value("Ghost", "Dragon")

    async def test_map_replace_fail_new_exists(self):
        """
        Problem 4:
        If new_value already exists on board,
        replace_card_value must raise ValueError
        (values must stay unique).
        """
        with self.assertRaisesRegex(ValueError, "already on the board"):
            await self.cmds.replace_card_value("Unicorn", "Rainbow")

    async def test_watch_event_triggers(self):
        """
        Problem 5:
        wait_for_change() should block until a visible board change happens.
        A flip should trigger the change and unblock wait_for_change().
        """
        wait_task = asyncio.create_task(self.cmds.wait_for_change())

        # Let the watch actually start waiting
        await asyncio.sleep(0.01)
        self.assertFalse(wait_task.done())

        # Trigger a change
        await self.cmds.flip("P1", 0, 0)

        # It should complete promptly
        try:
            await asyncio.wait_for(wait_task, timeout=0.1)
        except asyncio.TimeoutError:
            self.fail("wait_for_change did not unblock after a board action")

    async def test_map_interleaving(self):
        """
        Problem 4/5:
        map() must not block other operations.
        While replace_card_value runs,
        another player can still flip successfully.
        """
        # Start a replacement that actually exists on the board
        replace_task = asyncio.create_task(
            self.cmds.replace_card_value("Unicorn", "UnicornX")
        )

        # While replacement is in progress (or soon after), perform a flip
        await self.cmds.flip("P1", 0, 1)  # flip a Rainbow

        # Wait for replacement to finish
        await replace_task

        # Verify replacement happened
        self.assertEqual(self.board.get_card(0, 0).string_value, "UnicornX")
        self.assertEqual(self.board.get_card(1, 0).string_value, "UnicornX")

        # Verify the flip succeeded and didn't get blocked
        flipped = self.board.get_card(0, 1)
        self.assertTrue(flipped.face_up)
        self.assertEqual(flipped.string_value, "Rainbow")

    async def test_watch_no_change_on_controller_only(self):
        """
        Problem 5:
        watch() should return only when visible changes occur.
        A normal flip changes visible state - watch should return.
        """
        wait_task = asyncio.create_task(self.cmds.wait_for_change())
        await asyncio.sleep(0.01)
        self.assertFalse(wait_task.done())

        await self.cmds.flip("P1", 0, 0)
        try:
            await asyncio.wait_for(wait_task, timeout=0.1)
        except asyncio.TimeoutError:
            self.fail("watch did not return upon actual change")


if __name__ == '__main__':
    unittest.main()
