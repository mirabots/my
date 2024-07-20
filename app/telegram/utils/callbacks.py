from aiogram.filters.callback_data import CallbackData


def get_choosed_callback_text(keyboards, callback_data) -> str:
    for keyboard in keyboards:
        for button in keyboard:
            if button.callback_data == callback_data:
                return button.text


class CallbackAbort(CallbackData, prefix="abort"):
    action: str


class CallbackAnimeChoose(CallbackData, prefix="anime"):
    id: int


class CallbackAnimeAdd(CallbackData, prefix="anime_add"):
    pass


class CallbackAnimeAction(CallbackData, prefix="anime_action"):
    id: int
    action: str
