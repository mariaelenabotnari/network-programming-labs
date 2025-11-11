from typing import Optional


class Card:
    def __init__(self, string_value: str, face_down: bool = True,
                 face_up: bool = False, removed: bool = False) -> None:
        self._string_value = string_value
        self._face_down = face_down
        self._face_up = face_up
        self._removed = removed
        self._controller: Optional[str] = None
        self._matched: bool = False

        self.checkRep()

    def checkRep(self) -> None:
        """
        REQUIRES:
            - None

        MODIFIES:
            - None

        EFFECTS:
            - Ensures:
                * not (face_up and face_down)
                * if removed:
                    - face_up is False
                    - controller is None

        THROWS:
            - AssertionError if representation violated
        """
        assert not (self._face_up and self._face_down), \
            "Card cannot be face_up and face_down at the same time."

        if self._removed:
            assert not self._face_up, "Removed cards must not be face_up."
            assert self._controller is None, "Removed cards cannot be controlled."

    @property
    def string_value(self) -> str:
        return self._string_value

    @string_value.setter
    def string_value(self, value: str):
        self._string_value = value

    @property
    def face_down(self) -> bool:
        return self._face_down

    @face_down.setter
    def face_down(self, value: bool):
        self._face_down = value

    @property
    def face_up(self) -> bool:
        return self._face_up

    @face_up.setter
    def face_up(self, value: bool):
        self._face_up = value

    @property
    def removed(self) -> bool:
        return self._removed

    @removed.setter
    def removed(self, value: bool):
        self._removed = value

    @property
    def player_id(self) -> Optional[str]:
        return self._player_id

    @player_id.setter
    def player_id(self, value: Optional[str]):
        self._player_id = value

    @property
    def controller(self) -> Optional[str]:
        return self._controller

    @controller.setter
    def controller(self, value: Optional[str]):
        self._controller = value

    @property
    def matched(self) -> bool:
        return self._matched

    @matched.setter
    def matched(self, value: bool):
        self._matched = value

    def __str__(self) -> str:
        if self.removed:
            return "_"
        elif self.face_up:
            return self.string_value
        else:
            return "*"
