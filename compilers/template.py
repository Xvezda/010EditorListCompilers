# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


import re
import struct
import os.path

import logging
logger = logging.getLogger(__name__)

from .base import _010EditorListCompiler


class TemplateObject(object):
    def __init__(self, filename, name=None, mask=None, source=None):
        self.filename = filename
        self.name = name or self.filename
        self.mask = mask or ''
        self.options = {
            'visible': True,
            'run_on_load': True,
            'show_editor_on_load': False
        }
        self.source = source or ''


class TemplateListCompiler(_010EditorListCompiler):
    """Template list compiler for 010 Editor."""
    EXT_ARGS = ('t',)
    MAGIC_ARGS = ('T',)
    DEF_NAME = 'TemplateList'

    def __init__(self):
        super().__init__()
        self._buffer = b''

    def write(self, writable):
        writable.write(self._buffer)

    def add(self, filename, name=None, mask=None, source=None):
        super().add(TemplateObject(
            filename,
            name,
            mask,
            source,
        ))

    def add_file(self, filename):
        with open(filename, 'r', encoding='iso-8859-1') as f:
            name = os.path.basename(os.path.splitext(filename)[0]) or filename
            filename_ = '($TEMPLATEDIR)/%s' % os.path.basename(filename)
            source = self.unix2dos(f.read()) + '\n'
            mask = self.search_mask(source)
            # Add template object
            self.add(filename_, name, mask, source)

    def _write(self, b):
        try:
            self._buffer += b
        except TypeError:
            self._buffer += b.encode()

    def _tell(self):
        return len(self._buffer)

    def compile(self):
        self._write_header()
        # Write each template object metadata
        self._write_metadatas()
        self._write_entries()
        self._write_files()
        # Write End Of File signature
        self._write_eof()

    def _write_header(self):
        # Write magic numbers
        self._write(self.MAGIC)
        # Write total count
        self._write(struct.pack('<I', len(self)))

    def _write_metadatas(self):
        for template in iter(self):
            options = {**template.options}
            # Write name length, name
            self._write(struct.pack('<I', len(template.name)))
            self._write(self.str2wstr(template.name))
            # Write mask length, mask
            self._write(struct.pack('<I', len(template.mask)))
            self._write(self.str2wstr(template.mask))
            # Write visibility flag
            self._write(struct.pack('<I', int(options.get('visible', True))))
            # Write filename length, filename
            self._write(struct.pack('<I', len(template.filename)))
            self._write(self.str2wstr(template.filename))
            # Write "run on load" option
            self._write(
                struct.pack('<I', int(options.get('run_on_load', True))))
            # Write "show editor on load" option
            self._write(
                struct.pack('<I', int(options.get('show_editor_on_load', False))))

    def _write_entries(self):
        # File datas starting after offset and filesize datas.
        # So, offset begins at
        # = current_offset + total_count * (offset<4byte> + filesize <4byte>)
        calculated_offset = self._tell() + len(self) * 8
        # Repeat loop for writing offset, filesize
        for template in iter(self):
            # Write offset
            self._write(struct.pack('<I', calculated_offset))
            # Write filesize
            # Don't know why, but actual value is +1
            filesize = len(template.source) + 1
            self._write(struct.pack('<I', filesize))
            # Increase offset
            calculated_offset += filesize

    def _write_files(self):
        # Final loop
        for template in iter(self):
            # Write source
            self._write(template.source.encode())

    def _write_eof(self):
        self._write(self.EOF)

    def __len__(self):
        return len(list(iter(self)))


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

