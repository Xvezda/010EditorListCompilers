# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


import os.path
import logging
logger = logging.getLogger(__name__)

import pydantic

from .compiler import (
    _010EditorListCompiler,
    ListOptionObject,
    ListFileObject,
)


class TemplateOptionObject(ListOptionObject):
    pass


class TemplateObject(ListFileObject):
    options: TemplateOptionObject


class TemplateListCompiler(_010EditorListCompiler):
    """Template list compiler for 010 Editor."""
    EXT_ARGS = ('t',)
    MAGIC_ARGS = ('T',)
    DEF_NAME = 'TemplateList'

    def parse(self, stream):
        name = os.path.basename(os.path.splitext(stream.name)[0])
        # TODO: Follow list import options
        filename_ = '($TEMPLATEDIR)/%s' % os.path.basename(stream.name)
        source = self.unix2dos(stream.read()) + '\n'
        mask = self.search_mask(source)
        options = TemplateOptionObject()

        return TemplateObject(
            filename=filename_,
            name=name,
            mask=mask,
            source=source,
            options=options
        )

    def _write_metadatas(self) -> None:
        for template in iter(self):
            options = {**template.options.dict()}
            # Write name length, name
            self._write_metadata(template.name)
            # Write mask length, mask
            self._write_metadata(template.mask)
            # Write visibility flag
            self._write_uint32(options.get('visible'))
            # Write filename length, filename
            self._write_metadata(template.filename)
            # Write "run on load" option
            self._write_uint32(options.get('run_on_load'))
            # Write "show editor on load" option
            self._write_uint32(options.get('show_editor_on_load'))


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

