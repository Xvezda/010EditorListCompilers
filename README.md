# 010EditorListCompilers

A third-party compiler to build binary file which used for [010 Editor](https://www.sweetscape.com/010editor/) configuration.


## Usage

```sh
python3 -m o1olistcompiler template ..path/to/binary-templates/*.bt
```

## Synopsis

List files, which used in 010 Editor to store preferences of scripts and templates.

| feature   | filename | list filename |
|-----------|----------|---------------|
| script    | `*.1sc`  | `*.1sl`       |
| template  | `*.bt`   | `*.1tl`       |

010 Editor list files can be import and exported,
but its hard to add multiple new scripts and templates at once
since there is no such exported list file composed with unknown new files.
(Don't know why there isn't installation feature exists... :shrug:)

Also, list files are in binary format and it makes hard to modify simply.

This python package will helps you to solve these kind of issues.


## Requirements

Checkout `requirements.txt` and interpreter version `>= Python 3.8`.

