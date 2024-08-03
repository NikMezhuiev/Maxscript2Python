#! /usr/bin/env python3
"""
Program to transfom maxscript code to python code.
"""
# pylint: disable=invalid-name, import-error
import re
import os
import sys
from parsec import ParseError
import mxsp
import pyout
import mxscp
#from mxs2py.log import eprint



# def main():
#     """
#     Main program
#     All (optional) args are file name.
#     If no args are provided the code operates on stdin.
#     """
#     if len(sys.argv) > 1:
#         for fname in sys.argv[1:]:
#             with open(fname, encoding="utf-8") as f:
#                 buf = f.read().replace("\r\n", "\n")
#                 buf = preprocess(buf, fname)
#                 with open("outfile", "w", encoding="utf-8") as of:
#                     of.write(buf)
#                 (output, error) = topy(buf, f"Automatically converted {fname}")
#                 if error is not None:
#                     sys.exit(-1)
#                 print(output)
#     else:
#         inputstr = sys.stdin.read()
#         (output, error) = topy(inputstr, "Automatically converted stdin")
#         if error is not None:
#             sys.exit(-1)
#         print(output)
#         sys.exit(0)
#
# if __name__ == "__main__":
#     main()
