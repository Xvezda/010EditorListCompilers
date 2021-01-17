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


class TemplateObject(object):
    def __init__(self, filename, name=None, mask=None, source=None):
        self.filename = filename
        self.name = name or self.filename
        self.mask = mask or ''
        self.options = {
            'run_on_load': False,
            'show_editor_on_load': False
        }
        self.source = source or ''


# TODO: Add abstract compiler class
class TemplateListCompiler(object):
    """Template list compiler for 010 Editor."""
    EXT = '1tl'
    EOF = b'%EOF\x01\x00\x00\x00'
    MAGIC = b'%1TL=\x00\x00\x00'

    def __init__(self):
        self.templates = []

    @staticmethod
    def _search_mask(data):
        search = re.search(
            r'^(?:/[*/])?\s*File Mask:\s*([^\s]+)(?:\*/)?\s*$',
            data,
            re.M
        )
        if not search:
            return ''
        return search.group(1)

    @staticmethod
    def _unix2dos(data):
        return re.sub(r'\r{2,}', '\r', data.replace('\n', '\r\n'), re.M)

    def add(self, filename, name=None, mask=None, source=None):
        self.templates.append(TemplateObject(
            filename,
            name,
            mask,
            source,
        ))

    def add_file(self, filename):
        with open(filename, 'r') as f:
            name = os.path.basename(os.path.splitext(filename)[0]) or filename
            filename_ = '($TEMPLATEDIR)/%s' % os.path.basename(filename)
            source = self._unix2dos(f.read()) + '\n'
            mask = self._search_mask(source)
            # Add template object
            self.add(filename_, name, mask, source)

    def compile(self):
        # TODO: Fix hard coded filename
        with open(f'TemplateList.{self.EXT}', 'wb') as f:
            total_count = len(self.templates)
            wchars = lambda w: b''.join(map(lambda b: struct.pack('<H', ord(b)), list(w)))

            # Write magic numbers
            f.write(self.MAGIC)
            # Write total count
            f.write(struct.pack('<I', total_count))
            # Write each template object metadata
            for template in self.templates:
                # Write name length, name
                f.write(struct.pack('<I', len(template.name)))
                f.write(wchars(template.name))
                # Write mask length, mask
                f.write(struct.pack('<I', len(template.mask)))
                f.write(wchars(template.mask))
                # Unknown 4 byte
                f.write(struct.pack('<I', 1))
                # Write filename length, filename
                f.write(struct.pack('<I', len(template.filename)))
                f.write(wchars(template.filename))
                # TODO: Apply template object option
                # Write "run on load" option
                f.write(struct.pack('<I', 1))
                # Write "show editor on load" option
                f.write(struct.pack('<I', 0))

            # File datas starting after offset and filesize datas.
            # So, offset begins at
            # = current_offset + total_count * (offset<4byte> + filesize <4byte>)
            calculated_offset = f.tell() + total_count * 8
            # Repeat loop for writing offset, filesize
            for template in self.templates:
                # Write offset
                f.write(struct.pack('<I', calculated_offset))
                # Write filesize
                # Don't know why, but actual value is +1
                filesize = len(template.source) + 1
                f.write(struct.pack('<I', filesize))
                # Increase offset
                calculated_offset += filesize

            # Final loop
            for template in self.templates:
                # Write source
                f.write(template.source.encode('utf-8'))

            # Write End Of File signature
            f.write(self.EOF)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    compiler = TemplateListCompiler()
    for filename in getattr(args, 'files', []):
        compiler.add_file(filename)
    compiler.compile()

