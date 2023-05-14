# SPDX-FileCopyrightText: Copyright 2023 Neradoc, https://neradoc.me
# SPDX-License-Identifier: MIT
"""
UF2 docs here:
https://github.com/microsoft/uf2#file-format
"""
import sys
import click
from pathlib import Path

def slim_files(file_in, file_out):
    data_out = []

    with open(file_in, "rb") as finput:
        num = 0
        block_index = 0
        while data := bytearray(finput.read(512)):
            magic = data[0:4]
            if magic != b"UF2\n":
                print(num, "bad magic", magic)
            payload_size = int.from_bytes(data[16:20], "little")
            # print(num, payload_size)
            payload = data[32: 32 + payload_size]
            do_write = False
            for byte in payload:
                if byte != 0xFF:
                    do_write = True
                    break
            if do_write:
                data[20:24] = (block_index).to_bytes(4, "little")
                data_out.append(data)
                block_index += 1
                # foutput.write(data)
            num += 1

    # 
    print(f"Blocks: {block_index}/{num} Size: {256 * block_index:,} B")

    with open(file_out, "wb") as foutput:
        for data in data_out:
            data[24:28] = (block_index).to_bytes(4, "little")
            foutput.write(data)

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
    "--force", "-f",
    is_flag=True,
    help="Overwrite output file if it exists."
)
def main(file_in, file_out, force):
    """
    Slim down a UF2 file by removing the blocks that are all FF.
    This assumes that it will be flashed on a previously erased or brand new flash chip.

    The output file will be automatically named by appending ".slim" to the name.
    """
    if file_out is None:
        file_out = file_in.rstrip(".uf2") + ".slim.uf2"
    if Path(file_out).exists() and not force:
        click.secho(
            f"ERROR: Output file {file_out} already exists !\n"
            "Use -f to overwrite anyway.",
            fg="red"
        )
        sys.exit(1)
    slim_files(file_in, file_out)

main()
