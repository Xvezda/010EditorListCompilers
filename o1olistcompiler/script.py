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


class ScriptOptionObject(ListOptionObject):
    run_on_startup: bool = False
    run_on_shutdown: bool = False


class ScriptObject(ListFileObject):
    options: ScriptOptionObject


class ScriptListCompiler(_010EditorListCompiler):
    """Script list compiler for 010 Editor."""
    EXT_ARGS = ('s',)
    MAGIC_ARGS = ('S',)
    DEF_NAME = 'ScriptList'

    def parse(self, stream):
        name = os.path.basename(os.path.splitext(stream.name)[0])
        # TODO: Follow list import options
        filename_ = '($SCRIPTDIR)/%s' % os.path.basename(stream.name)
        source = self.unix2dos(stream.read()) + '\n'
        mask = self.search_mask(source)
        options = ScriptOptionObject()

        return ScriptObject(
            filename=filename_,
            name=name,
            mask=mask,
            source=source,
            options=options
        )

    def _write_metadatas(self) -> None:
        for script in iter(self):
            options = {**script.options.dict()}
            # Write name length, name
            self._write_metadata(script.name)
            # Write visibility flag
            self._write_uint32(options.get('visible'))
            # Write filename length, filename
            self._write_metadata(script.filename)
            # Write "run on load" option
            self._write_uint32(options.get('run_on_load'))
            # Write "show editor on load" option
            self._write_uint32(options.get('show_editor_on_load'))
            # Write mask length, mask
            self._write_metadata(script.mask)
            # Write "run on startup" option
            self._write_uint32(options.get('run_on_startup'))
            # Write "run on shutdown" option
            self._write_uint32(options.get('run_on_shutdown'))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('files', nargs='+')
    args = parser.parse_args()

    compiler = ScriptListCompiler()
    for filename in getattr(args, 'files', []):
        compiler.add_file(filename)
    compiler.save(args.output)


