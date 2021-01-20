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
from typing import (
    Optional, Any, AnyStr, BinaryIO
)

import logging
logger = logging.getLogger(__name__)

import pydantic

from .base import _010EditorListCompiler


class TemplateOptionObject(pydantic.BaseModel):
    visible: bool = True
    run_on_load: bool = True
    show_editor_on_load: bool = False


class TemplateObject(pydantic.BaseModel):
    filename: str
    name: str
    mask: Optional[str]
    options = TemplateOptionObject()
    source: Optional[str]


class TemplateListCompiler(_010EditorListCompiler):
    """Template list compiler for 010 Editor."""
    EXT_ARGS = ('t',)
    MAGIC_ARGS = ('T',)
    DEF_NAME = 'TemplateList'

    def __init__(self):
        super().__init__()
        self._buffer = io.BytesIO()

    def write(self, writable: BinaryIO):
        writable.write(self.link())

    def add(self, *,
            filename: str, name: str, mask: str, source: str) -> None:
        tmplobj = TemplateObject(
            filename=filename,
            name=name,
            mask=mask,
            source=source
        )
        super().add(tmplobj)

    def add_file(self, filename: str) -> None:
        with open(filename, 'r', encoding='iso-8859-1') as f:
            name = os.path.basename(os.path.splitext(filename)[0]) or filename
            filename_ = '($TEMPLATEDIR)/%s' % os.path.basename(filename)
            source = self.unix2dos(f.read()) + '\n'
            mask = self.search_mask(source)
            # Add template object
            self.add(filename=filename_, name=name, mask=mask, source=source)

    def _write(self, b: AnyStr) -> None:
        try:
            self._buffer.write(b)
        except TypeError:
            self._buffer.write(b.encode())

    def _write_u32(self, data: Any) -> None:
        self._write(struct.pack('<I', int(data)))

    def _tell(self) -> int:
        return self._buffer.tell()

    def compile(self) -> None:
        self._write_header()
        # Write each template object metadata
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
        self._write_u32(len(self))

    def _write_metadatas(self) -> None:
        for template in iter(self):
            options = {**template.options.dict()}
            # Write name length, name
            self._write_u32(len(template.name))
            self._write(self.str2wstr(template.name))
            # Write mask length, mask
            self._write_u32(len(template.mask))
            self._write(self.str2wstr(template.mask))
            # Write visibility flag
            self._write_u32(options.get('visible', True))
            # Write filename length, filename
            self._write_u32(len(template.filename))
            self._write(self.str2wstr(template.filename))
            # Write "run on load" option
            self._write_u32(options.get('run_on_load', True))
            # Write "show editor on load" option
            self._write_u32(options.get('show_editor_on_load', False))

    def _write_entries(self) -> None:
        # File datas starting after offset and filesize datas.
        # So, offset begins at
        # = current_offset + total_count * (offset<4byte> + filesize <4byte>)
        calculated_offset = self._tell() + len(self) * 8
        # Repeat loop for writing offset, filesize
        for template in iter(self):
            # Write offset
            self._write_u32(calculated_offset)
            # Write filesize
            # Don't know why, but actual value is +1
            filesize = len(template.source) + 1
            self._write_u32(filesize)
            # Increase offset
            calculated_offset += filesize

    def _write_files(self) -> None:
        for template in iter(self):
            # Write source
            self._write(template.source.encode())

    def _write_eof(self) -> None:
        self._write(self.EOF)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    compiler = TemplateListCompiler()
    for filename in getattr(args, 'files', []):
        compiler.add_file(filename)
    compiler.save(args.output)

