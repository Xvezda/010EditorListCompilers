# Copyright (c) 2021 Xvezda <xvezda@naver.com>
#
# Use of this source code is governed by an MIT-style
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.


def main():
    from . import __all__
    import importlib
    import argparse
    parser = argparse.ArgumentParser()

    def usage():
        parser.print_help()
        parser.exit(1)

    available_list_compilers = [
        clsname[:-len('ListCompiler')].lower() for clsname in __all__
    ]

    parser.add_argument('--output', '-o', type=str)
    parser.add_argument('compiler',
                        choices=available_list_compilers,
                        type=str)
    parser.add_argument('files', nargs='+')

    args = parser.parse_args()
    compiler_name = args.compiler
    mod = importlib.import_module('.' + compiler_name, package=__package__)
    try:
        mod_main = getattr(mod, '_main')
    except AttributeError:
        import sys
        print(f"compiler name '{compiler_name}' "
              'seems does not support command line client', file=sys.stderr)
        parser.exit(1)
    mod_main(args)


if __name__ == '__main__':
    main()

