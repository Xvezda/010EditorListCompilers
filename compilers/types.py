# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


from typing import Protocol
import pydantic


class Compilable(Protocol):
    pass


class Seekable(Protocol):
    def seekable(self) -> bool:
        pass


class ObjectFile(pydantic.BaseModel):
    pass


