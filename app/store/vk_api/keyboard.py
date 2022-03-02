from typing import Optional


class ButtonColor:
    red = "negative"
    green = "positive"
    blue = "primary"
    white = "secondary"


class Button:
    type: str
    color: str

    def as_dict(self) -> dict:
        return dict(action={k: v for k, v in self.__dict__.items() if k != "color"},
                    color=self.color)


class TextButton(Button):

    def __init__(self, label: str, payload: Optional[dict] = None, color=ButtonColor.white):
        super().__init__()
        self.type = "text"
        self.label = label
        self.payload = payload or {}
        self.color = color


class CallbackButton(Button):

    def __init__(self, label: str, payload: Optional[dict] = None, color=ButtonColor.white):
        super().__init__()
        self.type = "callback"
        self.label = label
        self.payload = payload or {}
        self.color = color


class Keyboard:

    def __init__(self, one_time=False, inline=False, buttons: list[list[Button]] = None):
        self.one_time = one_time
        self.inline = inline
        self.buttons = buttons or []

    def add(self, buttons: list[Button]) -> None:
        assert type(buttons) is list
        self.buttons.append(buttons)

    def as_dict(self) -> dict:
        return dict(one_time=self.one_time,
                    inline=self.inline,
                    buttons=[[i.as_dict() for i in row] for row in self.buttons])
