# SPDX-FileCopyrightText: Copyright 2023 Neradoc, https://neradoc.me
# SPDX-License-Identifier: MIT
"""
UF2 docs here:
https://github.com/microsoft/uf2#file-format
"""
import sys
import click
from pathlib import Path

BLOCK_ADDR = 12
PAYLOAD_SIZE = 16
BLOCK_IDX = 20
BLOCK_NUM = 24
PAYLOAD = 32


def slim_files(file_in, file_out, blocknum=True):
    data_out = []
    bnum = 0
    addr0 = 0

    with open(file_in, "rb") as finput:
        num = 0
        block_index = 0
        while data := bytearray(finput.read(512)):
            magic = data[0:4]
            if magic != b"UF2\n":
                print(num, "bad magic", magic)
                sys.exit(2)
            payload_size = int.from_bytes(
                data[PAYLOAD_SIZE : PAYLOAD_SIZE + 4], "little"
            )
            # print(num, payload_size)
            payload = data[PAYLOAD : PAYLOAD + payload_size]
            do_write = False
            for byte in payload:
                if byte != 0xFF:
                    do_write = True
                    break

            addr = int.from_bytes(data[BLOCK_ADDR : BLOCK_ADDR + 4], "little")
            if addr0 > 0 and addr != addr0 + 0x100:
                print(f"addr {addr0} {addr}")
            addr0 = addr

            bbnum = int.from_bytes(data[BLOCK_IDX : BLOCK_IDX + 4], "little")
            if bbnum > 0 and bbnum != bnum + 1:
                print(bnum, bbnum)
            bnum = bbnum

            if do_write:
                if blocknum:
                    data[BLOCK_IDX : BLOCK_IDX + 4] = (block_index).to_bytes(
                        4, "little"
                    )
                data_out.append(data)
                if len(data) != 512:
                    raise ValueError("WTF")
                block_index += 1
            num += 1

    import binascii

    num_blocks_bytes = (block_index).to_bytes(4, "little")
    print(f"Blocks: {block_index}/{num} Size: {256 * block_index:,} B")
    # print(binascii.hexlify(num_blocks_bytes))

    with open(file_out, "wb") as foutput:
        for data in data_out:
            if blocknum:
                data[BLOCK_NUM : BLOCK_NUM + 4] = num_blocks_bytes
            if len(data) != 512:
                raise ValueError("WTF")
            num = foutput.write(data)
            if num != 512:
                raise ValueError("WTF")


@click.command()
@click.argument(
    "file_in",
    required=True,
)
@click.argument(
    "file_out",
    required=False,
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite output file if it exists.",
)
@click.option(
    "--blocknum/--noblocknum",
    "-b/-B",
    is_flag=True,
    default=None,
    help="Write new block number values (default true).",
)
def main(file_in, file_out, force, blocknum):
    """
    Slim down a UF2 file by removing the blocks that are all FF.
    This assumes that it will be flashed on a previously erased or brand new flash chip.

    The output file will be automatically named by appending ".slim" to the name.
    """
    if blocknum is None:
        blocknum = True
    if file_out is None:
        file_out = file_in.rstrip(".uf2") + ".slim.uf2"
    if Path(file_out).exists() and not force:
        click.secho(
            f"ERROR: Output file {file_out} already exists !\n"
            "Use -f to overwrite anyway.",
            fg="red",
        )
        sys.exit(1)
    slim_files(file_in, file_out, blocknum)


main()
