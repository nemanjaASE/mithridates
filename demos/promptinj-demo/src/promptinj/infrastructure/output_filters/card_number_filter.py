"""Output check for full card numbers. A backstop: the context should not contain them."""
import re

# A PAN is 13–19 digits. Models break them up in all sorts of ways, so a run of digits
# separated by at most two "formatting" characters each still counts as one number.
_SEPARATORS = r"[ \t\r\n.\- –—]"
_PAN_RUN = re.compile(rf"(?<!\d)(?:\d{_SEPARATORS}{{0,2}}){{13,19}}(?!\d)")


class CardNumberFilter:
    """Blocks an answer that contains a full card number.

    Matches 13 to 19 digits, each optionally followed by up to two spaces, tabs, newlines,
    dots or dashes. Does not match masked numbers (`****4421`), numbers written as words,
    or encoded or reversed numbers.
    """

    def inspect(self, text: str) -> str | None:
        """Checks the answer for a full card number.

        Args:
            text: The model's answer.

        Returns:
            The block reason, or None if the answer contains no card number.
        """
        if _PAN_RUN.search(text):
            return "response contains a full card number"
        return None
