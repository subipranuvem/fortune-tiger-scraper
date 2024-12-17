from logging import Logger

from babel.numbers import format_currency


class BalancePrinter:
    @staticmethod
    def print_balance(logger: Logger, balance_in_cents: int) -> None:
        formatted_balance = format_currency(
            balance_in_cents / 100, "BRL", locale="pt_BR"
        )
        logger.info(f"actual balance: R${formatted_balance}")
