# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


import abc
import typing
import re
import struct


class Compiler(object, metaclass=abc.ABCMeta):
    def __init__(self):
        super().__init__()

    @abc.abstractmethod
    def add(self, *args, **kwds):
        pass

    @abc.abstractmethod
    def compile(self, *args, **kwds):
        pass

    @abc.abstractmethod
    def save(self, *args, **kwds):
        pass

    @abc.abstractmethod
    def write(self, *args, **kwds):
        pass


class _010EditorListCompiler(Compiler):
    EOF = b'%EOF\x01\x00\x00\x00'
    EXT_FMT = '1{}l'
    MAGIC_FMT = '%1{}L=\x00\x00\x00'

    def __init__(self):
        super().__init__()
        self._iterable = []
        self._setattrs()

    def _setattrs(self):
        fmt_suffix = '_FMT'
        args_suffix = '_ARGS'
        for attr in dir(self):
            if attr.endswith(fmt_suffix):
                fmt = getattr(self, attr)
                prefix = attr[:-len(fmt_suffix)]
                setattr(self, prefix,
                        fmt.format(*getattr(self, prefix + args_suffix)))

    @typing.overload
    def compile(self, *args, **kwds):
        pass

    def add(self, obj):
        self._iterable.append(obj)

    def save(self, filename=None):
        if filename and not filename.endswith(self.EXT):
            filename += '.' + self.EXT
        elif not filename:
            filename = '.'.join([self.DEF_NAME, self.EXT])
        self.compile()
        with open(filename, 'wb') as f:
            self.write(f)

    @typing.overload
    def write(self, *args, **kwds):
        pass

    @classmethod
    def search_metadata(cls, key, data):
        regexp = r'^(?:/[*/])?\s*%s:\s*([^\s]+)(?:\*/)?\s*$'
        search = re.search(regexp % re.escape(key), data, re.M)
        if not search:
            return ''
        return search.group(1)

    @classmethod
    def search_mask(cls, data):
        return cls.search_metadata('File Mask', data)

    @classmethod
    def chr2wchr(cls, chr_):
        return struct.pack('<H', ord(chr_))

    @classmethod
    def str2wstr(cls, str_):
        return b''.join(map(cls.chr2wchr, list(str_)))

    @staticmethod
    def unix2dos(data):
        return re.sub(r'\r{2,}', '\r', data.replace('\n', '\r\n'), re.M)

    def __iter__(self):
        return iter(self._iterable)

    def __len__(self):
        return len(list(iter(self)))

