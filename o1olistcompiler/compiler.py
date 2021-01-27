# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import io
import re
import struct
import os.path
import contextlib
import typing
from typing import (
    Optional, Any, AnyStr, BinaryIO
)

import pydantic

from .base import (
    Abstract010EditorListCompiler,
    BASEBIT_SIZE
)
from .types import ObjectFile


class ListOptionObject(pydantic.BaseModel):
    # Follow 010Editor defaults
    visible: bool = True
    run_on_load: bool = True
    show_editor_on_load: bool = False


class ListFileObject(ObjectFile):
    filename: str
    name: Optional[str]
    mask: Optional[str]
    options: ListOptionObject
    source: Optional[str]


class _010EditorListCompiler(Abstract010EditorListCompiler):
    OFFSET_SIZE = BASEBIT_SIZE
    FILE_LEN_SIZE = BASEBIT_SIZE

    def __init__(self):
        super().__init__()
        self._buffer = io.BytesIO()

    def write(self, writable: BinaryIO):
        writable.write(self.link())

    def add(self, fileobj) -> None:
        super().add(fileobj)

    def add_file(self, filename: str) -> None:
        with open(filename, 'r', encoding='iso-8859-1') as f:
            self.add(self.parse(f))

    def _write(self, b: AnyStr) -> None:
        try:
            self._buffer.write(b)
        except TypeError:
            self._buffer.write(b.encode())

    def _write_uint32(self, data: Any) -> None:
        self._write(struct.pack('<I', int(data)))

    def _tell(self) -> int:
        return self._buffer.tell()

    def compile(self) -> None:
        self._write_header()
        # Write each file object metadata
        self._write_metadatas()
        self._write_entries()
        self._write_files()
        # Write End Of File signature
        self._write_eof()

    @staticmethod
    @contextlib.contextmanager
    def _restoring_position(*args, **kwds):
        seekable = args[0] if args else kwds['seekable']
        offset = seekable.tell()
        seekable.seek(0)
        try:
            yield seekable
        finally:
            seekable.seek(offset)

    def link(self) -> bytes:
        with self._restoring_position(self._buffer) as b:
            return b.read()

    def _write_header(self) -> None:
        # Write magic numbers
        self._write(self.MAGIC)
        # Write total count
        self._write_uint32(len(self))

    def _write_metadata(self, data) -> None:
        # Write name length, name
        self._write_uint32(len(data))
        self._write(self.str2wstr(data))

    @typing.overload
    def _write_metadatas(self) -> None:
        raise NotImplementedError

    def _write_entries(self) -> None:
        # File datas starting after offset and filesize datas.
        calculated_offset = self._tell() + (
            len(self) * (self.OFFSET_SIZE + self.FILE_LEN_SIZE)
        )
        # Repeat loop for writing offset, filesize
        for fileobj in iter(self):
            # Write offset
            self._write_uint32(calculated_offset)
            # Write filesize
            # Don't know why, but actual value is +1
            filesize = len(fileobj.source) + 1
            self._write_uint32(filesize)
            # Increase offset
            calculated_offset += filesize

    def _write_files(self) -> None:
        for fileobj in iter(self):
            # Write source
            self._write(fileobj.source.encode())

    def _write_eof(self) -> None:
        self._write(self.EOF)

