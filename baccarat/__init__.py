# baccarat-math - exact 8-deck baccarat mathematics
# Copyright (c) 2026 EdgeLV | https://edgelv.com | Telegram @bacc_ai
# Released under the MIT License. Keep this notice in redistributions.
"""Exact baccarat mathematics: enumeration, risk of ruin, staking systems.

Project : baccarat-math
Author  : EdgeLV
Web     : https://edgelv.com
Contact : Telegram @bacc_ai
License : MIT
"""
__version__ = "1.0.0"
__author__ = "EdgeLV"
__url__ = "https://edgelv.com"
__contact__ = "Telegram @bacc_ai"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2026 EdgeLV"

SOURCE_NOTICE = (
    f"baccarat-math v{__version__} | {__copyright__} | {__url__} | {__contact__}"
)


def print_source_notice() -> None:
    """Print the provenance line that closes every command-line run."""
    print()
    print("-" * 78)
    print(SOURCE_NOTICE)
    print("Interactive versions of these tables: https://edgelv.com/en/tools/")
