import logging

import click
from dotenv import load_dotenv
from web3 import Web3

from .uniswap import Uniswap, AddressLike, _str_to_addr
from .tokens import tokens


logger = logging.getLogger(__name__)


def _coerce_to_checksum(addr: str) -> str:
    if not addr.startswith("0x"):
        if addr.upper() in tokens:
            return tokens[addr.upper()]
        else:
            raise ValueError(
                "token was not an address, and a shorthand was not found in the token db"
            )
    if Web3.isChecksumAddress(addr):
        return addr
    else:
        # logger.warning("Address wasn't in checksum format, coercing")
        return Web3.toChecksumAddress(addr)  # type: ignore


@click.group()
@click.option("-v", "--verbose", is_flag=True)
def main(verbose: bool) -> None:
    logging.basicConfig(level=logging.INFO if verbose else logging.WARNING)
    load_dotenv()


@main.command()
@click.argument("token_in", type=_coerce_to_checksum)
@click.argument("token_out", type=_coerce_to_checksum)
@click.option(
    "--raw",
    is_flag=True,
    help="Don't normalize the quoted price to the input tokens's decimals",
)
@click.option(
    "--quantity",
    help="Quantity of output tokens to get price of. Falls back to one full unit of the output by default (10**18 for WETH, for example).",
)
def price(
    token_in: AddressLike, token_out: AddressLike, raw: bool, quantity: int = None
) -> None:
    """Returns the price of ``quantity`` tokens of ``token_out`` quoted in ``token_in``."""
    uni = Uniswap(None, None, version=2)
    if quantity is None:
        quantity = 10 ** uni.get_token(token_out)["decimals"]
    price = uni.get_token_token_output_price(token_in, token_out, qty=quantity)
    if raw:
        print(price)
    else:
        decimals = uni.get_token(token_in)["decimals"]
        print(price / 10 ** decimals)


@main.command()
@click.argument("token", type=_coerce_to_checksum)
def token(token: AddressLike) -> None:
    uni = Uniswap(None, None, version=2)
    t1 = uni.get_token(token)
    print(t1)


@main.command()
@click.option("--metadata", is_flag=True, help="Also get metadata for tokens")
def tokendb(metadata: bool) -> None:
    """List known token addresses"""
    uni = Uniswap(None, None, version=2)
    for symbol, addr in tokens.items():
        if metadata:
            data = uni.get_token(_str_to_addr(addr))
            data["address"] = addr
            assert data["symbol"].lower() == symbol.lower()
            print(data)
        else:
            print({"symbol": symbol, "address": addr})