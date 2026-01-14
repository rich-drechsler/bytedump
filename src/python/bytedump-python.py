#!/usr/bin/python3
#
# Copyright (C) 2025-2026 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)
# SPDX-License-Identifier: MIT
#
# ----------------------------------------------------------------------
# Ported to Python in collaboration with Google Gemini (December 2025)
# ----------------------------------------------------------------------
#
# NOTE - lots of noise if you run pylint on this file and there still are issues that
# I'm going to investigate. Right now I use something like
#
#   pylint --disable=C0103,C0114,C0115,C0116,C0301,C0302,E1136,E1137,R0904,R0912,R0914,R0915,R1702 bytedump-python.py
#
# to run pylint (version 2.12.2) on my Linux system. Disabled messages are things I've
# decided to permanently ignore or looked at (briefly at least) and may revisit in the
# near future.
#

import inspect
import locale
import os
import re
import sys

from io import BytesIO, StringIO, UnsupportedOperation
from typing import Any, BinaryIO

###################################
#
# ByteDump - Main Class
#
###################################

class ByteDump:
    """
    Python reproduction of the bash bytedump script (Python Translation).
    """

    ###################################
    #
    # ByteDump Variables
    #
    ###################################

    #
    # Program information.
    #

    PROGRAM_VERSION: str = "0.4"
    PROGRAM_DESCRIPTION: str = "Python reproduction of the Java bytedump program"
    PROGRAM_COPYRIGHT: str = "Copyright (C) 2025-2026 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)"
    PROGRAM_LICENSE: str = "SPDX-License-Identifier: MIT"

    #
    # The string assigned to PROGRAM_NAME constant is only used in error and usage
    # messages.
    #

    PROGRAM_NAME: str = os.path.basename(sys.argv[0])

    #
    # PROGRAM_USAGE is currently only if when there's no available help text, either
    # in a resource file, a string, or any other mechanism (e.g., a custom formatted
    # block of comment).
    #

    PROGRAM_USAGE: str = "Usage: " + PROGRAM_NAME + " [OPTIONS] [FILE|-]"

    #
    # Overall dump settings.
    #

    DUMP_field_flags: int = 0
    DUMP_input_read: int = 0
    DUMP_input_maxbuf: int = 0xFFFF
    DUMP_input_start: int = 0
    DUMP_layout: str = "WIDE"
    DUMP_layout_default: str = "WIDE"
    DUMP_output_start: int = 0
    DUMP_record_length: int = 16
    DUMP_record_length_limit: int = 4096
    DUMP_record_separator: str = "\n"
    DUMP_unexpanded_char: str = "?"

    #
    # Values associated with the ADDR, BYTE, and TEXT fields in our dump. Some of
    # them are changed by command line options, while many others are used or set
    # by the initialization code that runs after all of the options are processed.
    #

    ADDR_output: str = "HEX-LOWER"
    ADDR_digits: int = 0
    ADDR_field_flag: int = 0x01
    ADDR_field_separator: str = " "
    ADDR_field_separator_size: int = 1
    ADDR_format: str = ""
    ADDR_format_width: str = ""
    ADDR_format_width_default: str = "6"
    ADDR_format_width_default_xxd: str = "08"
    ADDR_format_width_limit: int = 0
    ADDR_padding: str = " "
    ADDR_prefix: str = ""
    ADDR_prefix_size: int = 0
    ADDR_radix: int = -1
    ADDR_suffix: str = ":"
    ADDR_suffix_size: int = 1

    BYTE_output: str = "HEX-LOWER"
    BYTE_digits_per_octet: int = -1
    BYTE_field_flag: int = 0x02
    BYTE_field_separator: str = "  "
    BYTE_field_width: int = 0
    BYTE_indent: str = ""
    BYTE_map: str = ""
    BYTE_prefix: str = ""
    BYTE_prefix_size: int = 0
    BYTE_separator: str = " "
    BYTE_separator_size: int = 1
    BYTE_suffix: str = ""
    BYTE_suffix_size: int = 0

    TEXT_output: str = "ASCII"
    TEXT_chars_per_octet: int = -1
    TEXT_field_flag: int = 0x04
    TEXT_indent: str = ""
    TEXT_map: str = ""
    TEXT_prefix: str = ""
    TEXT_prefix_size: int = 0
    TEXT_separator: str = ""
    TEXT_separator_size: int = 0
    TEXT_suffix: str = ""
    TEXT_suffix_size: int = 0
    TEXT_unexpanded_string: str = ""

    #
    # Debugging keys that can be changed by command line options. None of them are
    # officially documented, but they are occasionally referenced in comments that
    # you'll find in the source code.
    #

    DEBUG_background: bool = False
    DEBUG_bytemap: bool = False
    DEBUG_foreground: bool = False
    DEBUG_settings: bool = False
    DEBUG_textmap: bool = False

    #
    # The value assigned to DEBUG_settings_prefixes are the space separated prefixes
    # of the variable names that are dumped when the --debug=settings option is used.
    # Change the list if you want a different collection of "settings" or have them
    # presented in a different order.
    #

    DEBUG_settings_prefixes: str = "DUMP ADDR BYTE TEXT DEBUG PROGRAM"

    #
    # The ASCII_TEXT_MAP mapping array is designed to reproduce the ASCII text output
    # that xxd (and other similar programs) generate. Unprintable ASCII characters and
    # all bytes with their top bit set are represented by a period in the TEXT field.
    #
    # NOTE - even though they're Python lists the ones that are used to map individual
    # bytes (i.e., the numbers) to the strings that are supposed to appear in the TEXT
    # and BYTE fields in our dump will be called "mapping arrays" rather than "mapping
    # lists".
    #

    ASCII_TEXT_MAP: list[str] = [
        #
        # Basic Latin Block (ASCII)
        #

           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",

        "\\u0020",  "\\u0021",  "\\u0022",  "\\u0023",  "\\u0024",  "\\u0025",  "\\u0026",  "\\u0027",
        "\\u0028",  "\\u0029",  "\\u002A",  "\\u002B",  "\\u002C",  "\\u002D",  "\\u002E",  "\\u002F",
        "\\u0030",  "\\u0031",  "\\u0032",  "\\u0033",  "\\u0034",  "\\u0035",  "\\u0036",  "\\u0037",
        "\\u0038",  "\\u0039",  "\\u003A",  "\\u003B",  "\\u003C",  "\\u003D",  "\\u003E",  "\\u003F",
        "\\u0040",  "\\u0041",  "\\u0042",  "\\u0043",  "\\u0044",  "\\u0045",  "\\u0046",  "\\u0047",
        "\\u0048",  "\\u0049",  "\\u004A",  "\\u004B",  "\\u004C",  "\\u004D",  "\\u004E",  "\\u004F",
        "\\u0050",  "\\u0051",  "\\u0052",  "\\u0053",  "\\u0054",  "\\u0055",  "\\u0056",  "\\u0057",
        "\\u0058",  "\\u0059",  "\\u005A",  "\\u005B",  "\\u005C",  "\\u005D",  "\\u005E",  "\\u005F",
        "\\u0060",  "\\u0061",  "\\u0062",  "\\u0063",  "\\u0064",  "\\u0065",  "\\u0066",  "\\u0067",
        "\\u0068",  "\\u0069",  "\\u006A",  "\\u006B",  "\\u006C",  "\\u006D",  "\\u006E",  "\\u006F",
        "\\u0070",  "\\u0071",  "\\u0072",  "\\u0073",  "\\u0074",  "\\u0075",  "\\u0076",  "\\u0077",
        "\\u0078",  "\\u0079",  "\\u007A",  "\\u007B",  "\\u007C",  "\\u007D",  "\\u007E",     ".",

        #
        # Latin-1 Supplement Block
        #

           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",

           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
    ]

    #
    # The UNICODE_TEXT_MAP mapping array is a modified version of the ASCII mapping
    # array that expands the collection of bytes displayed by unique single character
    # strings to the printable characters in Unicode's Latin-1 Supplement Block. All
    # control characters are displayed using the string ".", exactly the way they're
    # handled in the ASCII_TEXT_MAP mapping array.
    #

    UNICODE_TEXT_MAP: list[str] = [
        #`
        # Basic Latin Block (ASCII)
        #

           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",

        "\\u0020",  "\\u0021",  "\\u0022",  "\\u0023",  "\\u0024",  "\\u0025",  "\\u0026",  "\\u0027",
        "\\u0028",  "\\u0029",  "\\u002A",  "\\u002B",  "\\u002C",  "\\u002D",  "\\u002E",  "\\u002F",
        "\\u0030",  "\\u0031",  "\\u0032",  "\\u0033",  "\\u0034",  "\\u0035",  "\\u0036",  "\\u0037",
        "\\u0038",  "\\u0039",  "\\u003A",  "\\u003B",  "\\u003C",  "\\u003D",  "\\u003E",  "\\u003F",
        "\\u0040",  "\\u0041",  "\\u0042",  "\\u0043",  "\\u0044",  "\\u0045",  "\\u0046",  "\\u0047",
        "\\u0048",  "\\u0049",  "\\u004A",  "\\u004B",  "\\u004C",  "\\u004D",  "\\u004E",  "\\u004F",
        "\\u0050",  "\\u0051",  "\\u0052",  "\\u0053",  "\\u0054",  "\\u0055",  "\\u0056",  "\\u0057",
        "\\u0058",  "\\u0059",  "\\u005A",  "\\u005B",  "\\u005C",  "\\u005D",  "\\u005E",  "\\u005F",
        "\\u0060",  "\\u0061",  "\\u0062",  "\\u0063",  "\\u0064",  "\\u0065",  "\\u0066",  "\\u0067",
        "\\u0068",  "\\u0069",  "\\u006A",  "\\u006B",  "\\u006C",  "\\u006D",  "\\u006E",  "\\u006F",
        "\\u0070",  "\\u0071",  "\\u0072",  "\\u0073",  "\\u0074",  "\\u0075",  "\\u0076",  "\\u0077",
        "\\u0078",  "\\u0079",  "\\u007A",  "\\u007B",  "\\u007C",  "\\u007D",  "\\u007E",     ".",

        #
        # Latin-1 Supplement Block
        #

           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",
           ".",        ".",        ".",        ".",        ".",        ".",        ".",        ".",

        "\\u00A0",  "\\u00A1",  "\\u00A2",  "\\u00A3",  "\\u00A4",  "\\u00A5",  "\\u00A6",  "\\u00A7",
        "\\u00A8",  "\\u00A9",  "\\u00AA",  "\\u00AB",  "\\u00AC",  "\\u00AD",  "\\u00AE",  "\\u00AF",
        "\\u00B0",  "\\u00B1",  "\\u00B2",  "\\u00B3",  "\\u00B4",  "\\u00B5",  "\\u00B6",  "\\u00B7",
        "\\u00B8",  "\\u00B9",  "\\u00BA",  "\\u00BB",  "\\u00BC",  "\\u00BD",  "\\u00BE",  "\\u00BF",
        "\\u00C0",  "\\u00C1",  "\\u00C2",  "\\u00C3",  "\\u00C4",  "\\u00C5",  "\\u00C6",  "\\u00C7",
        "\\u00C8",  "\\u00C9",  "\\u00CA",  "\\u00CB",  "\\u00CC",  "\\u00CD",  "\\u00CE",  "\\u00CF",
        "\\u00D0",  "\\u00D1",  "\\u00D2",  "\\u00D3",  "\\u00D4",  "\\u00D5",  "\\u00D6",  "\\u00D7",
        "\\u00D8",  "\\u00D9",  "\\u00DA",  "\\u00DB",  "\\u00DC",  "\\u00DD",  "\\u00DE",  "\\u00DF",
        "\\u00E0",  "\\u00E1",  "\\u00E2",  "\\u00E3",  "\\u00E4",  "\\u00E5",  "\\u00E6",  "\\u00E7",
        "\\u00E8",  "\\u00E9",  "\\u00EA",  "\\u00EB",  "\\u00EC",  "\\u00ED",  "\\u00EE",  "\\u00EF",
        "\\u00F0",  "\\u00F1",  "\\u00F2",  "\\u00F3",  "\\u00F4",  "\\u00F5",  "\\u00F6",  "\\u00F7",
        "\\u00F8",  "\\u00F9",  "\\u00FA",  "\\u00FB",  "\\u00FC",  "\\u00FD",  "\\u00FE",  "\\u00FF",
    ]

    #
    # The CARET_TEXT_MAP mapping array maps bytes into printable two character strings
    # that can be used in the TEXT field display. The two character strings assigned to
    # bytes that are Unicode C0 and C1 control codes (and DEL) start with a caret (^)
    # and end with a printable character that's selected using:
    #
    #       Unicode C0 and DEL: (byte + 0x40) % 0x80
    #               Unicode C1: (byte + 0x40) % 0x80 + 0x80
    #
    # The rest of the bytes in the array are printable and the string assigned to each
    # one starts with a space and ends with the Unicode character that represents that
    # byte. The extension of "caret notation" beyond the ASCII block seems reasonable,
    # but as far as I know it's just my own convention.
    #

    CARET_TEXT_MAP: list[str] = [
        #
        # Basic Latin Block (ASCII)
        #

        "^\\u0040",  "^\\u0041",  "^\\u0042",  "^\\u0043",  "^\\u0044",  "^\\u0045",  "^\\u0046",  "^\\u0047",
        "^\\u0048",  "^\\u0049",  "^\\u004A",  "^\\u004B",  "^\\u004C",  "^\\u004D",  "^\\u004E",  "^\\u004F",
        "^\\u0050",  "^\\u0051",  "^\\u0052",  "^\\u0053",  "^\\u0054",  "^\\u0055",  "^\\u0056",  "^\\u0057",
        "^\\u0058",  "^\\u0059",  "^\\u005A",  "^\\u005B",  "^\\u005C",  "^\\u005D",  "^\\u005E",  "^\\u005F",

        " \\u0020",  " \\u0021",  " \\u0022",  " \\u0023",  " \\u0024",  " \\u0025",  " \\u0026",  " \\u0027",
        " \\u0028",  " \\u0029",  " \\u002A",  " \\u002B",  " \\u002C",  " \\u002D",  " \\u002E",  " \\u002F",
        " \\u0030",  " \\u0031",  " \\u0032",  " \\u0033",  " \\u0034",  " \\u0035",  " \\u0036",  " \\u0037",
        " \\u0038",  " \\u0039",  " \\u003A",  " \\u003B",  " \\u003C",  " \\u003D",  " \\u003E",  " \\u003F",
        " \\u0040",  " \\u0041",  " \\u0042",  " \\u0043",  " \\u0044",  " \\u0045",  " \\u0046",  " \\u0047",
        " \\u0048",  " \\u0049",  " \\u004A",  " \\u004B",  " \\u004C",  " \\u004D",  " \\u004E",  " \\u004F",
        " \\u0050",  " \\u0051",  " \\u0052",  " \\u0053",  " \\u0054",  " \\u0055",  " \\u0056",  " \\u0057",
        " \\u0058",  " \\u0059",  " \\u005A",  " \\u005B",  " \\u005C",  " \\u005D",  " \\u005E",  " \\u005F",
        " \\u0060",  " \\u0061",  " \\u0062",  " \\u0063",  " \\u0064",  " \\u0065",  " \\u0066",  " \\u0067",
        " \\u0068",  " \\u0069",  " \\u006A",  " \\u006B",  " \\u006C",  " \\u006D",  " \\u006E",  " \\u006F",
        " \\u0070",  " \\u0071",  " \\u0072",  " \\u0073",  " \\u0074",  " \\u0075",  " \\u0076",  " \\u0077",
        " \\u0078",  " \\u0079",  " \\u007A",  " \\u007B",  " \\u007C",  " \\u007D",  " \\u007E",  "^\\u003F",

        #
        # Latin-1 Supplement Block
        #

        "^\\u00C0",  "^\\u00C1",  "^\\u00C2",  "^\\u00C3",  "^\\u00C4",  "^\\u00C5",  "^\\u00C6",  "^\\u00C7",
        "^\\u00C8",  "^\\u00C9",  "^\\u00CA",  "^\\u00CB",  "^\\u00CC",  "^\\u00CD",  "^\\u00CE",  "^\\u00CF",
        "^\\u00D0",  "^\\u00D1",  "^\\u00D2",  "^\\u00D3",  "^\\u00D4",  "^\\u00D5",  "^\\u00D6",  "^\\u00D7",
        "^\\u00D8",  "^\\u00D9",  "^\\u00DA",  "^\\u00DB",  "^\\u00DC",  "^\\u00DD",  "^\\u00DE",  "^\\u00DF",

        " \\u00A0",  " \\u00A1",  " \\u00A2",  " \\u00A3",  " \\u00A4",  " \\u00A5",  " \\u00A6",  " \\u00A7",
        " \\u00A8",  " \\u00A9",  " \\u00AA",  " \\u00AB",  " \\u00AC",  " \\u00AD",  " \\u00AE",  " \\u00AF",
        " \\u00B0",  " \\u00B1",  " \\u00B2",  " \\u00B3",  " \\u00B4",  " \\u00B5",  " \\u00B6",  " \\u00B7",
        " \\u00B8",  " \\u00B9",  " \\u00BA",  " \\u00BB",  " \\u00BC",  " \\u00BD",  " \\u00BE",  " \\u00BF",
        " \\u00C0",  " \\u00C1",  " \\u00C2",  " \\u00C3",  " \\u00C4",  " \\u00C5",  " \\u00C6",  " \\u00C7",
        " \\u00C8",  " \\u00C9",  " \\u00CA",  " \\u00CB",  " \\u00CC",  " \\u00CD",  " \\u00CE",  " \\u00CF",
        " \\u00D0",  " \\u00D1",  " \\u00D2",  " \\u00D3",  " \\u00D4",  " \\u00D5",  " \\u00D6",  " \\u00D7",
        " \\u00D8",  " \\u00D9",  " \\u00DA",  " \\u00DB",  " \\u00DC",  " \\u00DD",  " \\u00DE",  " \\u00DF",
        " \\u00E0",  " \\u00E1",  " \\u00E2",  " \\u00E3",  " \\u00E4",  " \\u00E5",  " \\u00E6",  " \\u00E7",
        " \\u00E8",  " \\u00E9",  " \\u00EA",  " \\u00EB",  " \\u00EC",  " \\u00ED",  " \\u00EE",  " \\u00EF",
        " \\u00F0",  " \\u00F1",  " \\u00F2",  " \\u00F3",  " \\u00F4",  " \\u00F5",  " \\u00F6",  " \\u00F7",
        " \\u00F8",  " \\u00F9",  " \\u00FA",  " \\u00FB",  " \\u00FC",  " \\u00FD",  " \\u00FE",  " \\u00FF",
    ]

    #
    # The CARET_ESCAPE_TEXT_MAP mapping array is a slightly modified version of the
    # CARET_TEXT_MAP array that uses C-style escape sequences, when they're defined,
    # to represent control characters. The remaining control characters are displayed
    # using the caret notation that's already been described.
    #

    CARET_ESCAPE_TEXT_MAP: list[str] = [
        #
        # Basic Latin Block (ASCII)
        #

             "\\0",  "^\\u0041",  "^\\u0042",  "^\\u0043",  "^\\u0044",  "^\\u0045",  "^\\u0046",       "\\a",
             "\\b",       "\\t",       "\\n",       "\\v",       "\\f",       "\\r",  "^\\u004E",  "^\\u004F",
        "^\\u0050",  "^\\u0051",  "^\\u0052",  "^\\u0053",  "^\\u0054",  "^\\u0055",  "^\\u0056",  "^\\u0057",
        "^\\u0058",  "^\\u0059",  "^\\u005A",  "^\\u005B",  "^\\u005C",  "^\\u005D",  "^\\u005E",  "^\\u005F",

        " \\u0020",  " \\u0021",  " \\u0022",  " \\u0023",  " \\u0024",  " \\u0025",  " \\u0026",  " \\u0027",
        " \\u0028",  " \\u0029",  " \\u002A",  " \\u002B",  " \\u002C",  " \\u002D",  " \\u002E",  " \\u002F",
        " \\u0030",  " \\u0031",  " \\u0032",  " \\u0033",  " \\u0034",  " \\u0035",  " \\u0036",  " \\u0037",
        " \\u0038",  " \\u0039",  " \\u003A",  " \\u003B",  " \\u003C",  " \\u003D",  " \\u003E",  " \\u003F",
        " \\u0040",  " \\u0041",  " \\u0042",  " \\u0043",  " \\u0044",  " \\u0045",  " \\u0046",  " \\u0047",
        " \\u0048",  " \\u0049",  " \\u004A",  " \\u004B",  " \\u004C",  " \\u004D",  " \\u004E",  " \\u004F",
        " \\u0050",  " \\u0051",  " \\u0052",  " \\u0053",  " \\u0054",  " \\u0055",  " \\u0056",  " \\u0057",
        " \\u0058",  " \\u0059",  " \\u005A",  " \\u005B",  " \\u005C",  " \\u005D",  " \\u005E",  " \\u005F",
        " \\u0060",  " \\u0061",  " \\u0062",  " \\u0063",  " \\u0064",  " \\u0065",  " \\u0066",  " \\u0067",
        " \\u0068",  " \\u0069",  " \\u006A",  " \\u006B",  " \\u006C",  " \\u006D",  " \\u006E",  " \\u006F",
        " \\u0070",  " \\u0071",  " \\u0072",  " \\u0073",  " \\u0074",  " \\u0075",  " \\u0076",  " \\u0077",
        " \\u0078",  " \\u0079",  " \\u007A",  " \\u007B",  " \\u007C",  " \\u007D",  " \\u007E",       "\\?",

        #
        # Latin-1 Supplement Block
        #

        "^\\u00C0",  "^\\u00C1",  "^\\u00C2",  "^\\u00C3",  "^\\u00C4",  "^\\u00C5",  "^\\u00C6",  "^\\u00C7",
        "^\\u00C8",  "^\\u00C9",  "^\\u00CA",  "^\\u00CB",  "^\\u00CC",  "^\\u00CD",  "^\\u00CE",  "^\\u00CF",
        "^\\u00D0",  "^\\u00D1",  "^\\u00D2",  "^\\u00D3",  "^\\u00D4",  "^\\u00D5",  "^\\u00D6",  "^\\u00D7",
        "^\\u00D8",  "^\\u00D9",  "^\\u00DA",  "^\\u00DB",  "^\\u00DC",  "^\\u00DD",  "^\\u00DE",  "^\\u00DF",

        " \\u00A0",  " \\u00A1",  " \\u00A2",  " \\u00A3",  " \\u00A4",  " \\u00A5",  " \\u00A6",  " \\u00A7",
        " \\u00A8",  " \\u00A9",  " \\u00AA",  " \\u00AB",  " \\u00AC",  " \\u00AD",  " \\u00AE",  " \\u00AF",
        " \\u00B0",  " \\u00B1",  " \\u00B2",  " \\u00B3",  " \\u00B4",  " \\u00B5",  " \\u00B6",  " \\u00B7",
        " \\u00B8",  " \\u00B9",  " \\u00BA",  " \\u00BB",  " \\u00BC",  " \\u00BD",  " \\u00BE",  " \\u00BF",
        " \\u00C0",  " \\u00C1",  " \\u00C2",  " \\u00C3",  " \\u00C4",  " \\u00C5",  " \\u00C6",  " \\u00C7",
        " \\u00C8",  " \\u00C9",  " \\u00CA",  " \\u00CB",  " \\u00CC",  " \\u00CD",  " \\u00CE",  " \\u00CF",
        " \\u00D0",  " \\u00D1",  " \\u00D2",  " \\u00D3",  " \\u00D4",  " \\u00D5",  " \\u00D6",  " \\u00D7",
        " \\u00D8",  " \\u00D9",  " \\u00DA",  " \\u00DB",  " \\u00DC",  " \\u00DD",  " \\u00DE",  " \\u00DF",
        " \\u00E0",  " \\u00E1",  " \\u00E2",  " \\u00E3",  " \\u00E4",  " \\u00E5",  " \\u00E6",  " \\u00E7",
        " \\u00E8",  " \\u00E9",  " \\u00EA",  " \\u00EB",  " \\u00EC",  " \\u00ED",  " \\u00EE",  " \\u00EF",
        " \\u00F0",  " \\u00F1",  " \\u00F2",  " \\u00F3",  " \\u00F4",  " \\u00F5",  " \\u00F6",  " \\u00F7",
        " \\u00F8",  " \\u00F9",  " \\u00FA",  " \\u00FB",  " \\u00FC",  " \\u00FD",  " \\u00FE",  " \\u00FF",
    ]

    #
    # The implementation that was generated by Gemini included explicit declarations
    # of all the BYTE field mapping arrays that were included here and basically were
    # trivial translations of the arrays declared in the Java version. Actually that's
    # not completely true, but it is what I eventually requested in the chat, primarily
    # to help me follow, test, and modify Gemini's implemetation. Anyway, the explicit
    # BYTE field mapping array declarations have been deleted, and instead the only one
    # the program needs is built (using list comprehension) in the initialize4_maps()
    # method.
    #
    # The next two variables will be end up being the references to the BYTE and TEXT
    # field mapping arrays that will be used to produce the dump that the user wants.
    # They're set in initialize4_maps(), and if either one ends up as None the code
    # that generates the dump will omit that field. Both fields can't be omitted.
    #

    byte_map: list[str] | None = None
    text_map: list[str] | None = None

    #
    # Values stored in the ANSI_ESCAPE dictionary are the ANSI escape sequences used
    # to selectively change the foreground and background attributes (think colors)
    # of character strings displayed in the BYTE and TEXT fields. They're used in
    # initialize5_attributes() to surround individual character strings in the BYTE
    # or TEXT field mapping arrays with the ANSI escape sequences that enable and
    # then disable (i.e., reset) the requested attribute.
    #
    # Values assigned to the keys defined in ANSI_ESCAPE that start with FOREGROUND
    # are ANSI escape sequences that set foreground attributes, while values assigned
    # to the keys that start with BACKGROUND are ANSI escapes that set the background
    # attributes. Take a look at
    #
    #     https://en.wikipedia.org/wiki/ANSI_escape_code
    #
    # if you want more information about ANSI escape codes.
    #

    ANSI_ESCAPE: dict[str, str] = {
        #
        # Foregound color escape sequences.
        #

        "FOREGROUND.black": "\u001B[30m",
        "FOREGROUND.red": "\u001B[31m",
        "FOREGROUND.green": "\u001B[32m",
        "FOREGROUND.yellow": "\u001B[33m",
        "FOREGROUND.blue": "\u001B[34m",
        "FOREGROUND.magenta": "\u001B[35m",
        "FOREGROUND.cyan": "\u001B[36m",
        "FOREGROUND.white": "\u001B[37m",

        "FOREGROUND.alt-black": "\u001B[90m",
        "FOREGROUND.alt-red": "\u001B[91m",
        "FOREGROUND.alt-green": "\u001B[92m",
        "FOREGROUND.alt-yellow": "\u001B[93m",
        "FOREGROUND.alt-blue": "\u001B[94m",
        "FOREGROUND.alt-magenta": "\u001B[95m",
        "FOREGROUND.alt-cyan": "\u001B[96m",
        "FOREGROUND.alt-white": "\u001B[97m",

        "FOREGROUND.bright-black": "\u001B[1;30m",
        "FOREGROUND.bright-red": "\u001B[1;31m",
        "FOREGROUND.bright-green": "\u001B[1;32m",
        "FOREGROUND.bright-yellow": "\u001B[1;33m",
        "FOREGROUND.bright-blue": "\u001B[1;34m",
        "FOREGROUND.bright-magenta": "\u001B[1;35m",
        "FOREGROUND.bright-cyan": "\u001B[1;36m",
        "FOREGROUND.bright-white": "\u001B[1;37m",

        #
        # Blinking foreground color escape sequences.
        #

        "FOREGROUND.blink-black": "\u001B[5;30m",
        "FOREGROUND.blink-red": "\u001B[5;31m",
        "FOREGROUND.blink-green": "\u001B[5;32m",
        "FOREGROUND.blink-yellow": "\u001B[5;33m",
        "FOREGROUND.blink-blue": "\u001B[5;34m",
        "FOREGROUND.blink-magenta": "\u001B[5;35m",
        "FOREGROUND.blink-cyan": "\u001B[5;36m",
        "FOREGROUND.blink-white": "\u001B[5;37m",

        "FOREGROUND.blink-alt-black": "\u001B[5;90m",
        "FOREGROUND.blink-alt-red": "\u001B[5;91m",
        "FOREGROUND.blink-alt-green": "\u001B[5;92m",
        "FOREGROUND.blink-alt-yellow": "\u001B[5;93m",
        "FOREGROUND.blink-alt-blue": "\u001B[5;94m",
        "FOREGROUND.blink-alt-magenta": "\u001B[5;95m",
        "FOREGROUND.blink-alt-cyan": "\u001B[5;96m",
        "FOREGROUND.blink-alt-white": "\u001B[5;97m",

        "FOREGROUND.blink-bright-black": "\u001B[5;1;30m",
        "FOREGROUND.blink-bright-red": "\u001B[5;1;31m",
        "FOREGROUND.blink-bright-green": "\u001B[5;1;32m",
        "FOREGROUND.blink-bright-yellow": "\u001B[5;1;33m",
        "FOREGROUND.blink-bright-blue": "\u001B[5;1;34m",
        "FOREGROUND.blink-bright-magenta": "\u001B[5;1;35m",
        "FOREGROUND.blink-bright-cyan": "\u001B[5;1;36m",
        "FOREGROUND.blink-bright-white": "\u001B[5;1;37m",

        #
        # The ANSI escape code that restores the default foreground color is
        #
        #    "\u001B[39m"
        #
        # but in our implementation, an empty string accomplishes the same thing, so
        # it's a much better choice.
        #

        "FOREGROUND.reset": "",

        #
        # Background color escape sequences - background blinking isn't possible.
        #

        "BACKGROUND.black": "\u001B[40m",
        "BACKGROUND.red": "\u001B[41m",
        "BACKGROUND.green": "\u001B[42m",
        "BACKGROUND.yellow": "\u001B[43m",
        "BACKGROUND.blue": "\u001B[44m",
        "BACKGROUND.magenta": "\u001B[45m",
        "BACKGROUND.cyan": "\u001B[46m",
        "BACKGROUND.white": "\u001B[47m",

        "BACKGROUND.alt-black": "\u001B[100m",
        "BACKGROUND.alt-red": "\u001B[101m",
        "BACKGROUND.alt-green": "\u001B[102m",
        "BACKGROUND.alt-yellow": "\u001B[103m",
        "BACKGROUND.alt-blue": "\u001B[104m",
        "BACKGROUND.alt-magenta": "\u001B[105m",
        "BACKGROUND.alt-cyan": "\u001B[106m",
        "BACKGROUND.alt-white": "\u001B[107m",

        "BACKGROUND.bright-black": "\u001B[1;40m",
        "BACKGROUND.bright-red": "\u001B[1;41m",
        "BACKGROUND.bright-green": "\u001B[1;42m",
        "BACKGROUND.bright-yellow": "\u001B[1;43m",
        "BACKGROUND.bright-blue": "\u001B[1;44m",
        "BACKGROUND.bright-magenta": "\u001B[1;45m",
        "BACKGROUND.bright-cyan": "\u001B[1;46m",
        "BACKGROUND.bright-white": "\u001B[1;47m",

        #
        # The ANSI escape code that restores the default background color is
        #
        #    "\u001B[49m"
        #
        # but in our implementation, an empty string accomplishes the same thing and
        # is a much better choice.
        #

        "BACKGROUND.reset": "",

        #
        # Reset all escape sequences. Omitting the 0 should work, but decided against
        # it - at least for now.
        #

        "RESET.attributes": "\u001B[0m"
    }

    #
    # This will be an instance of the AttributeTables class, but I didn't want that
    # class to be the first one in this file, which would have been required if the
    # AttributeTables class were mentioned at this point in the program. Instead of
    # doing the initialization here (the way it's done in Java version) moving it to
    # the setup() method means the only restriction on the AttributeTables class is
    # that it has to be defined before main() is called.
    #
    # TODO - even though it's not necessary, eventually consider doing the the same
    # thing in the Java version??
    #

    attribute_tables = None

    #
    # Using the arguments_consumed class variable means command line option can be
    # handled in a way that resembles the bash version of this program. There are
    # lots of alternatives, but this is appropriate for this program.
    #

    arguments_consumed: int = 0

    ###################################
    #
    # ByteDump Methods
    #
    ###################################

    @classmethod
    def arguments(cls, args: list[str]) -> None:
        input_stream: BinaryIO
        arg: str

        #
        # Expects at most one argument, which must be "-" or the name of a readable
        # file that's not a directory. Standard input is read when there aren't any
        # arguments or when "-" is the only argument. A representation of the bytes
        # in the input file are written to standard output in a style controlled by
        # the command line options.
        #
        # Treating "-" as an abbreviation for standard input, before checking to see
        # if it's the name of a readable file or directory in the current directory,
        # matches the way Linux commands typically handle it. A pathname containing
        # at least one "/" (e.g., ./-) is how to reference a file named "-" on the
        # command line.
        #

        if len(args) <= 1:
            arg = args[0] if len(args) > 0 else "-"
            if arg == "-" or os.access(arg, os.R_OK):
                if arg == "-" or not os.path.isdir(arg):
                    if arg != "-":
                        try:
                            #
                            # Want to read bytes from the file so we need to use "rb"
                            # when we open it.
                            #
                            input_stream = open(arg, "rb")
                            cls.dump(input_stream, sys.stdout)
                            input_stream.close()
                        except (FileNotFoundError, PermissionError):
                            cls.user_error("problem opening input file", arg)
                        except Exception as e:
                            cls.python_error(str(e))
                    else:
                        #
                        # Need to use sys.stdin.buffer if we expect to read bytes from
                        # standard input.
                        #
                        cls.dump(sys.stdin.buffer, sys.stdout)
                else:
                    cls.user_error("argument", delimit(arg), "is a directory")
            else:
                cls.user_error("argument", delimit(arg), "isn't a readable file")
        else:
            cls.user_error("too many non-option command line arguments:", delimit(args))

    @classmethod
    def byte_selector(cls, attribute: str, tokens: str, output: list[str | None]) -> None:
        base: int
        body: str
        chars: list[str | None]
        code: int
        count: int
        first: int
        index: int
        joined_chars: str
        last: int
        manager: RegexManager
        name: str
        prefix: str
        suffix: str
        tail: str
        tokens_start: str

        #
        # Called to parse a string that's supposed to assign an attribute (primarily
        # a color) to a group of bytes whenever any of them is displayed in the BYTE
        # or TEXT fields of the dump that this program produces. There's some simple
        # recursion used to implement "character classes" and "raw strings", but the
        # initial call is always triggered by a command line option.
        #
        # The first argument is a string that identifies the attribute that the user
        # wants applied to the bytes selected by the second argument. This method's
        # job is to figure out the numeric values of the selected bytes and associate
        # the attribute (i.e., the first argument) with each byte's numeric value in
        # the string array that's referenced by the third argument.
        #
        # The second argument is the byte "selector" and it's processed using regular
        # expressions. The selector consists of space separated tokens that represent
        # integers, integer ranges, character classes, and a modified implementation
        # of Rust raw string literals.
        #
        # A selector string that starts with an optional base prefix and is followed
        # by tokens that are completely enclosed in a single set of parentheses picks
        # the base used to evaluate all numbers in the selector. A base prefix that's
        # "0x" or "0X" means all numbers are hex, "0" means they're all octal, and no
        # base prefix (just the parens) means they're all decimal. Setting the default
        # base this way, instead of using an option, makes it easy for the user to do
        # exactly the same thing from the command line.
        #
        # If a base is set, all characters in an integer token must be digits in that
        # base. Otherwise C-style syntax is used, so hex integers start with "0x" or
        # "0X", octal integers start with "0", and decimal integers always start with
        # a nonzero decimal digit. An integer range is a pair of integers separated
        # by '-'. It represents a closed interval that extends from the left integer
        # to the right integer. Both end points of a range must be expressed in the
        # same base. Any integer or any part of an integer range that doesn't fit in
        # a byte is ignored.
        #
        # A character class uses a short, familiar lowercase name to select a group
        # of bytes. Those names must be bracketed by "[:" and ":]" in the selector
        # to be recognized as a character class. The 15 character classes that are
        # allowed in a selector are:
        #
        #     [:alnum:]      [:digit:]      [:punct:]
        #     [:alpha:]      [:graph:]      [:space:]
        #     [:blank:]      [:lower:]      [:upper:]
        #     [:cntrl:]      [:print:]      [:xdigit:]
        #
        #     [:ascii:]      [:latin1:]     [:all:]
        #
        # The first four rows are the 12 character classes that are defined in the
        # POSIX standard. The last row are 3 character classes that I decided to
        # support because they seemed like a convenient way to select familiar (or
        # otherwise obvious) blocks of contiguous bytes. This program only deals with
        # bytes, so it's easy to enumerate their members using integers and integer
        # ranges, and that's exactly how this method uses recursion to implement
        # character classes.
        #
        # A modified version of Rust's raw string literal can also be used as a token
        # in the byte selector. They always start with a prefix that's the letter 'r',
        # zero or more '#' characters, and a single or double quote, and they end with
        # a suffix that matches the quote and the number of '#' characters used in the
        # prefix. For example,
        #
        #       r"hello, world"
        #       r'hello, world'
        #      r#'hello, world'#
        #     r##"hello, world"##
        #
        # are valid selectors that represent exactly the same string. Any character,
        # except null, can appear in a raw string that's used as a selector, and the
        # selected bytes are the Unicode code points of the characters in the string
        # that are less than 256. Two quoting styles are supported because the quote
        # delimiters have to be protected from your shell on the command line.
        #
        # NOTE - this is a difficult method to follow, but similarity to what's done
        # in the other bytedump implementations should help if you decide to tackle
        # this method. Lots of regular expressions, but chatbots can help with them.
        #
        # NOTE - the RegexManager class defined later in this file saves a temporary
        # copy of the matched groups whenever the manager.matched() method succeeds.
        # Those groups can be accessed using the manager.cached_groups list and that
        # copy sticks around until the next call of manager.matched().
        #

        manager = RegexManager()
        base = 0

        #
        # First check for the optional base prefix.
        #

        if manager.matched(tokens, "^[ \\t]*(0[xX]?)?[(](.*)[)][ \\t]*$"):
            prefix = manager.cached_groups[1]
            tokens = manager.cached_groups[2]

            if prefix is None:
                base = 10
            elif prefix.lower() == "0x":
                base = 16
            elif prefix == "0":
                base = 8
            else:
                cls.internal_error("selector base prefix", delimit(prefix), "has not been implemented")

        while manager.matched(tokens, "^[ \\t]*([^ \\t].*)"):
            tokens = manager.cached_groups[1]
            tokens_start = tokens
            if manager.matched(tokens, "^(0[xX]?)?[0-9a-fA-F]"):
                first = 0
                last = -1
                if base > 0:
                    if base == 16:
                        if manager.matched(tokens, "^(([0-9a-fA-F]+)([-]([0-9a-fA-F]+))?)([ \\t]+|$)"):
                            first = int(manager.cached_groups[2], base)
                            last = int(manager.cached_groups[4], base) if manager.cached_groups[4] is not None else first
                            tokens = tokens[len(manager.cached_groups[0]):]
                        else:
                            cls.user_error("problem extracting a hex integer from", delimit(tokens_start))
                    elif base == 8:
                        if manager.matched(tokens, "^(([0-7]+)([-]([0-7]+))?)([ \\t]+|$)"):
                            first = int(manager.cached_groups[2], base)
                            last = int(manager.cached_groups[4], base) if manager.cached_groups[4] is not None else first
                            tokens = tokens[len(manager.cached_groups[0]):]
                        else:
                            cls.user_error("problem extracting an octal integer from", delimit(tokens_start))
                    elif base == 10:
                        if manager.matched(tokens, "^(([1-9][0-9]*)([-]([1-9][0-9]*))?)([ \\t]+|$)"):
                            first = int(manager.cached_groups[2], base)
                            last = int(manager.cached_groups[4], base) if manager.cached_groups[4] is not None else first
                            tokens = tokens[len(manager.cached_groups[0]):]
                        else:
                            cls.user_error("problem extracting a decimal integer from", delimit(tokens_start))
                    else:
                        cls.internal_error("base", delimit(str(base)), "has not been implemented")
                else:
                    if manager.matched(tokens, "^(0[xX]([0-9a-fA-F]+)([-]0[xX]([0-9a-fA-F]+))?)([ \\t]+|$)"):
                        first = int(manager.cached_groups[2], 16)
                        last = int(manager.cached_groups[4], 16) if manager.cached_groups[4] is not None else first
                        tokens = tokens[len(manager.cached_groups[0]):]
                    elif manager.matched(tokens, "^((0[0-7]*)([-](0[0-7]*))?)([ \\t]+|$)"):
                        first = int(manager.cached_groups[2], 8)
                        last = int(manager.cached_groups[4], 8) if manager.cached_groups[4] is not None else first
                        tokens = tokens[len(manager.cached_groups[0]):]
                    elif manager.matched(tokens, "^(([1-9][0-9]*)([-]([1-9][0-9]*))?)([ \\t]+|$)"):
                        first = int(manager.cached_groups[2], 10)
                        last = int(manager.cached_groups[4], 10) if manager.cached_groups[4] is not None else first
                        tokens = tokens[len(manager.cached_groups[0]):]
                    else:
                        cls.user_error("problem extracting an integer from", delimit(tokens_start))
                if first <= last and first < 256:
                    if last > 256:
                        last = 256
                    for index in range(first, last + 1):
                        output[index] = attribute
            elif manager.matched(tokens, "^\\[:"):
                if manager.matched(tokens, "^\\[:([a-zA-Z0-9]+):\\]([ \\t]+|$)"):
                    name = manager.cached_groups[1]
                    tokens = tokens[len(manager.cached_groups[0]):]

                    match name:
                        #
                        # POSIX character class names - these hex mappings were all generated
                        # by debugging code in the Java bytedump implementation.
                        #
                        case "alnum":
                            cls.byte_selector(attribute, "0x(30-39 41-5A 61-7A AA B5 BA C0-D6 D8-F6 F8-FF)", output)
                        case "alpha":
                            cls.byte_selector(attribute, "0x(41-5A 61-7A AA B5 BA C0-D6 D8-F6 F8-FF)", output)
                        case "blank":
                            cls.byte_selector(attribute, "0x(09 20 A0)", output)
                        case "cntrl":
                            cls.byte_selector(attribute, "0x(00-1F 7F-9F)", output)
                        case "digit":
                            cls.byte_selector(attribute, "0x(30-39)", output)
                        case "graph":
                            cls.byte_selector(attribute, "0x(21-7E A1-FF)", output)
                        case "lower":
                            cls.byte_selector(attribute, "0x(61-7A AA B5 BA DF-F6 F8-FF)", output)
                        case "print":
                            cls.byte_selector(attribute, "0x(20-7E A0-FF)", output)
                        case "punct":
                            cls.byte_selector(attribute, "0x(21-23 25-2A 2C-2F 3A-3B 3F-40 5B-5D 5F 7B 7D A1 A7 AB B6-B7 BB BF)", output)
                        case "space":
                            cls.byte_selector(attribute, "0x(09-0D 20 85 A0)", output)
                        case "upper":
                            cls.byte_selector(attribute, "0x(41-5A C0-D6 D8-DE)", output)
                        case "xdigit":
                            cls.byte_selector(attribute, "0x(30-39 41-46 61-66)", output)
                        #
                        # Custom character class names.
                        #
                        case "ascii":
                            cls.byte_selector(attribute, "0x(00-7F)", output)
                        case "latin1":
                            cls.byte_selector(attribute, "0x(80-FF)", output)
                        case "all":
                            cls.byte_selector(attribute, "0x(00-FF)", output)
                        case _:
                            cls.user_error(delimit(name), "is not the name of an implemented character class")
                else:
                    cls.user_error("problem extracting a character class from", delimit(tokens_start))
            elif manager.matched(tokens, "^(r([#]*)(\"|'))"):
                prefix = manager.cached_groups[1]
                suffix = manager.cached_groups[3] + manager.cached_groups[2]
                tokens = tokens[len(prefix):]
                if manager.matched(tokens, suffix + "(.*)"):
                    tail = manager.cached_groups[1]
                    if manager.matched(tail, "^([ \\t]|$)"):
                        body = tokens[:len(tokens) - (len(suffix) + len(tail))]
                        tokens = tail

                        chars = [None] * 256
                        count = 0
                        for index in range(len(body)):
                            code = ord(body[index])
                            if code < len(chars):
                                if chars[code] is None:
                                    count += 1
                                chars[code] = f"{code:02X}"

                        if count > 0:
                            joined_chars = " ".join([c for c in chars if c is not None])
                            cls.byte_selector(attribute, f"0x({joined_chars})", output)
                    else:
                        cls.user_error("all tokens must be space separated in byte selector", delimit(tokens_start))
            else:
                cls.user_error("no valid token found at the start of byte selector", delimit(tokens_start))

    @classmethod
    def debug(cls, *args: str) -> None:
        arg: str
        buffer: list[str]
        col: int
        consumed: dict[str, Any]
        key: str
        matched: list[str]
        prefix: str
        row: int
        tag: str
        value: Any

        #
        # Takes zero or more arguments that select debugging keys and handles the ones
        # that are supposed to generate immediate output and aren't explicilty handled
        # anywhere else in this class. No arguments selects the most important keys,
        # which currently happens to cover all the cases in the switch statement.
        #
        # NOTE - debug code in the bash version handled the dump of the background and
        # foreground attributes. I moved that responsibility to the dump_table() method
        # that's defined in the AttributeTables class.
        #

        if len(args) == 0:
            args = ("foreground", "background", "bytemap", "textmap", "settings")

        for arg in args:
            match arg:
                case "background":
                    if cls.DEBUG_background:
                        cls.attribute_tables.dump_table("BYTE_BACKGROUND", "[Debug] ")
                        cls.attribute_tables.dump_table("TEXT_BACKGROUND", "[Debug] ")

                case "bytemap":
                    if cls.DEBUG_bytemap:
                        if cls.byte_map is not None:
                            sys.stderr.write(f"[Debug] byte_map[{len(cls.byte_map)}]:\n")
                            for row in range(16):
                                prefix = "[Debug]    "
                                for col in range(16):
                                    sys.stderr.write(f"{prefix}{cls.byte_map[16 * row + col]}")
                                    prefix = " "
                                sys.stderr.write("\n")
                            sys.stderr.write("\n")

                case "foreground":
                    if cls.DEBUG_foreground:
                        cls.attribute_tables.dump_table("BYTE_FOREGROUND", "[Debug] ")
                        cls.attribute_tables.dump_table("TEXT_FOREGROUND", "[Debug] ")

                case "settings":
                    if cls.DEBUG_settings:
                        buffer = []
                        consumed = {}
                        for prefix in cls.DEBUG_settings_prefixes.split(" "):
                            matched = []
                            for key in dir(cls):
                                if key not in consumed and key.startswith(prefix):
                                    if hasattr(cls, key) and not callable(getattr(cls, key)):
                                        matched.append(key)
                                        consumed[key] = getattr(cls, key)

                            if len(matched) > 0:
                                matched.sort()
                                for key in matched:
                                    tag = "  "
                                    value = consumed[key]
                                    if value is None:
                                        buffer.append(f"[Debug] {tag} {key}=null\n")
                                    elif isinstance(value, str):
                                        buffer.append(f"[Debug] {tag} {key}=\"{value}\"\n")
                                    else:
                                        buffer.append(f"[Debug] {tag} {key}={str(value)}\n")
                                buffer.append("[Debug]\n")

                        sys.stderr.write(f"[Debug] Settings[{len(consumed)}]:\n")
                        sys.stderr.write("".join(buffer))
                        sys.stderr.write("\n")

                case "textmap":
                    if cls.DEBUG_textmap:
                        if cls.text_map is not None:
                            sys.stderr.write(f"[Debug] text_map[{len(cls.text_map)}]:\n")
                            for row in range(16):
                                prefix = "[Debug]    "
                                for col in range(16):
                                    sys.stderr.write(f"{prefix}{cls.text_map[16 * row + col]}")
                                    prefix = " "
                                sys.stderr.write("\n")
                            sys.stderr.write("\n")

    @classmethod
    def dump(cls, input_stream, output_stream) -> None:
        #
        # Responsible for important initialization, like seeking to the right spot in the
        # input_stream, loading the right number of bytes whenever the user wants to read
        # a fixed number from that stream, and then selecting the final method that's used
        # to generate the dump.
        #
        # NOTE - unlike the original bash version that usually postprocessed xxd output,
        # this program handles all the low level details and does care quite a bit about
        # performance. As a result there are methods that handle unusual dumps, like the
        # ones that want everything displayed as a single record or just want to see the
        # BYTE or TEXT fields. None of those methods make much of a difference, but some
        # careful code duplication seemed worthwhile. If you disagree it should be trivial
        # to have dump_all() handle almost everything.
        #

        try:
            if cls.DUMP_input_start > 0:
                try:
                    input_stream.seek(cls.DUMP_input_start)
                except UnsupportedOperation:
                    input_stream.read(cls.DUMP_input_start)
            if cls.DUMP_input_read > 0:
                input_stream = BytesIO(input_stream.read(cls.DUMP_input_read))

            if cls.DUMP_record_length > 0:
                if cls.DUMP_field_flags == cls.BYTE_field_flag:
                    cls.dump_byte_field(input_stream, output_stream)
                elif cls.DUMP_field_flags == cls.TEXT_field_flag:
                    cls.dump_text_field(input_stream, output_stream)
                else:
                    cls.dump_all(input_stream, output_stream)
            else:
                cls.dump_all_single_record(input_stream, output_stream)
        except IOError as e:
            cls.python_error(str(e))

    @classmethod
    def dump_all(cls, input_stream, output) -> None:
        addr_enabled: bool
        addr_format: str
        addr_prefix: str
        addr_suffix: str
        address: int
        buffer: bytes
        byte_enabled: bool
        byte_map: list[str] | None
        byte_pad_width: int
        byte_prefix: str
        byte_separator: str
        byte_suffix: str
        count: int
        record_len: int
        record_separator: str
        text_enabled: bool
        text_map: list[str] | None
        text_prefix: str
        text_separator: str
        text_suffix: str

        #
        # This is the primary dump method. Even though it can handle everything except
        # single record dumps, I decided to use separate methods (i.e., dump_byte_field()
        # and dump_text_field()) to the generate dumps that only include the BYTE or TEXT
        # fields. Each of those methods tries to eliminate a little of the overhead that
        # this method can't, and there's a chance that could occasionally be useful.
        #
        # NOTE - local variables are used to save frequently accessed values. They're an
        # attempt to squeeze out a little performance, because accessing local variables
        # should be a little faster than class variables. It's probably just a very small
        # optimization, but I didn't verify that claim in this bytedump implementation.
        #
        # NOTE - the selection of the method that's used to generate the actual dump is
        # made by dump(), so that's where to go if you want to modify my choices.
        #

        if cls.DUMP_record_length > 0:
            #
            # Compute strings used in the loop and make sure only local variables are used
            # in that loop. Accessing local variables should be slightly faster than class
            # variables.
            #
            addr_prefix = cls.ADDR_prefix
            addr_format = cls.ADDR_format
            addr_suffix = cls.ADDR_suffix + cls.ADDR_field_separator
            byte_prefix = cls.BYTE_indent + cls.BYTE_prefix
            byte_separator = cls.BYTE_separator
            byte_suffix = cls.BYTE_suffix + cls.BYTE_field_separator
            text_prefix = cls.TEXT_indent + cls.TEXT_prefix
            text_separator = cls.TEXT_separator
            text_suffix = cls.TEXT_suffix
            record_separator = cls.DUMP_record_separator
            record_len = cls.DUMP_record_length

            addr_enabled = (cls.ADDR_format is not None and len(cls.ADDR_format) > 0)
            byte_enabled = (cls.byte_map is not None)
            text_enabled = (cls.text_map is not None)

            byte_map = cls.byte_map
            text_map = cls.text_map

            # Pre-calculate padding width per byte
            byte_pad_width = 0
            if byte_enabled and cls.BYTE_field_width > 0:
                byte_pad_width = cls.BYTE_digits_per_octet + cls.BYTE_separator_size

            address = cls.DUMP_output_start

            while True:
                buffer = input_stream.read(record_len)
                count = len(buffer)
                if count <= 0:
                    break

                if addr_enabled:
                    output.write(addr_prefix)
                    output.write(addr_format % address)
                    output.write(addr_suffix)

                if byte_enabled:
                    output.write(byte_prefix)
                    output.write(byte_separator.join([byte_map[b] for b in buffer]))
                    if count < record_len and byte_pad_width > 0:
                        output.write(" " * ((record_len - count) * byte_pad_width))
                    output.write(byte_suffix)

                if text_enabled:
                    output.write(text_prefix)
                    output.write(text_separator.join([text_map[b] for b in buffer]))
                    output.write(text_suffix)

                output.write(record_separator)
                address += count

            output.flush()
        else:
            cls.internal_error("single record dump has not been handled properly")

    @classmethod
    def dump_all_single_record(cls, input_stream, output) -> None:
        addr_enabled: bool
        addr_format: str
        addr_prefix: str
        addr_suffix: str
        address: int
        buffer: bytes
        byte_enabled: bool
        byte_map: list[str] | None
        byte_separator: str
        chunk_size: int
        current_byte_prefix: str
        current_text_prefix: str
        looped: bool
        output_byte: Any
        output_text: Any
        text_enabled: bool
        text_map: list[str] | None
        text_separator: str

        #
        # Dumps the entire input file as a single record. The TEXT field must be buffered
        # (or saved in a temp file) when it and the BYTE field are supposed to be included
        # in the dump, otherwise TEXT field buffering can be skipped. This dump style won't
        # be used often.
        #

        output_byte = output
        if cls.byte_map is None or cls.text_map is None:
            output_text = output
        else:
            output_text = StringIO()

        if cls.DUMP_record_length == 0:
            addr_prefix = cls.ADDR_prefix
            addr_format = cls.ADDR_format
            addr_suffix = cls.ADDR_suffix + cls.ADDR_field_separator

            current_byte_prefix = cls.BYTE_indent + cls.BYTE_prefix
            byte_separator = cls.BYTE_separator

            current_text_prefix = cls.TEXT_indent + cls.TEXT_prefix
            text_separator = cls.TEXT_separator

            addr_enabled = (cls.ADDR_format is not None and len(cls.ADDR_format) > 0)
            byte_enabled = (cls.byte_map is not None)
            text_enabled = (cls.text_map is not None)

            byte_map = cls.byte_map
            text_map = cls.text_map

            chunk_size = 4096
            address = cls.DUMP_output_start
            looped = False

            while True:
                buffer = input_stream.read(chunk_size)
                if not buffer:
                    break

                if addr_enabled:
                    output.write(addr_prefix)
                    output.write(addr_format % address)
                    output.write(addr_suffix)
                    addr_enabled = False        # one record ==> one address

                if byte_enabled:
                    output_byte.write(current_byte_prefix)
                    output_byte.write(byte_separator.join([byte_map[b] for b in buffer]))
                    current_byte_prefix = byte_separator

                if text_enabled:
                    output_text.write(current_text_prefix)
                    output_text.write(text_separator.join([text_map[b] for b in buffer]))
                    current_text_prefix = text_separator

                looped = True

            if looped:
                if byte_enabled:
                    output.write(cls.BYTE_suffix + cls.BYTE_field_separator)
                    if text_enabled:
                        output.write(output_text.getvalue())
                        output.write(cls.TEXT_suffix)
                else:
                    output.write(cls.TEXT_suffix)

                output.write(cls.DUMP_record_separator)
                output.flush()
        else:
            cls.internal_error("this method can only be called to dump bytes as a single record")

    @classmethod
    def dump_byte_field(cls, input_stream, output) -> None:
        buffer: bytes
        byte_map: list[str] | None
        byte_prefix: str
        byte_separator: str
        byte_suffix: str
        complex_fmt: bool
        record_len: int
        record_separator: str

        #
        # Called to produce the dump when the BYTE field is the only field that's supposed
        # to appear in the output. It won't be used often and isn't even required, because
        # dump_all() can handle it. However, treating this as an obscure special case means
        # we can eliminate some overhead and that should make this run a little faster.
        #

        if cls.DUMP_record_length > 0:
            if cls.byte_map is not None:
                byte_map = cls.byte_map
                record_len = cls.DUMP_record_length

                complex_fmt = (len(cls.BYTE_separator) > 0 or len(cls.BYTE_prefix) > 0 or
                               len(cls.BYTE_indent) > 0 or len(cls.BYTE_suffix) > 0)

                if complex_fmt:
                    byte_prefix = cls.BYTE_indent + cls.BYTE_prefix
                    byte_separator = cls.BYTE_separator
                    byte_suffix = cls.BYTE_suffix + cls.DUMP_record_separator

                    while True:
                        buffer = input_stream.read(record_len)
                        if not buffer: break

                        output.write(byte_prefix)
                        output.write(byte_separator.join([byte_map[b] for b in buffer]))
                        output.write(byte_suffix)
                else:
                    record_separator = cls.DUMP_record_separator
                    while True:
                        buffer = input_stream.read(record_len)
                        if not buffer: break

                        output.write("".join([byte_map[b] for b in buffer]))
                        output.write(record_separator)

                output.flush()
            else:
                cls.internal_error("byte mapping array has not been initialized")
        else:
            cls.internal_error("single record dump has not been handled properly")

    @classmethod
    def dump_text_field(cls, input_stream, output) -> None:
        buffer: bytes
        complex_fmt: bool
        record_len: int
        record_separator: str
        text_map: list[str] | None
        text_prefix: str
        text_separator: str
        text_suffix: str

        #
        # Called to produce the dump when the TEXT field is the only field that's supposed
        # to appear in the output. It won't be used often and isn't even required, because
        # dump_all() can handle it. However, treating this as an obscure special case means
        # we can eliminate some overhead and that should make this run a little faster.
        #

        if cls.DUMP_record_length > 0:
            if cls.text_map is not None:
                text_map = cls.text_map
                record_len = cls.DUMP_record_length

                complex_fmt = (len(cls.TEXT_separator) > 0 or len(cls.TEXT_prefix) > 0 or
                               len(cls.TEXT_indent) > 0 or len(cls.TEXT_suffix) > 0)

                if complex_fmt:
                    text_prefix = cls.TEXT_indent + cls.TEXT_prefix
                    text_separator = cls.TEXT_separator
                    text_suffix = cls.TEXT_suffix + cls.DUMP_record_separator

                    while True:
                        buffer = input_stream.read(record_len)
                        if not buffer: break

                        output.write(text_prefix)
                        output.write(text_separator.join([text_map[b] for b in buffer]))
                        output.write(text_suffix)
                else:
                    record_separator = cls.DUMP_record_separator
                    while True:
                        buffer = input_stream.read(record_len)
                        if not buffer: break

                        output.write("".join([text_map[b] for b in buffer]))
                        output.write(record_separator)

                output.flush()
            else:
                cls.internal_error("text mapping array has not been initialized")
        else:
            cls.internal_error("single record dump has not been handled properly")

    @classmethod
    def help(cls) -> None:
        #
        # Really nothing much to do here - by the time this method is called the help
        # text we're supposed to display should be assigned to bytedump_help (using a
        # triple quoted string) and all we do here is print that string. bytedump_help
        # is currently initialized (with that string) right before the main() method
        # is called.
        #

        try:
            print(bytedump_help)
        except NameError:
            if cls.PROGRAM_USAGE is not None:
                print(cls.PROGRAM_USAGE)
                print()

    @classmethod
    def initialize(cls) -> None:
        #
        # Handles the initialization that happens after all the command line options
        # are processed. The goal is to try to honor all the user's requests and to
        # finish as many calculations as possible before starting the dump. Some of
        # those calculations are difficult, but I think what's done in this version
        # of bytedump is much easier to follow than the original bash implementation.
        #
        # All of the initialization could have been done right here in this method,
        # but there's so much code that splitting the work up into separate methods
        # seemed like a way to make it a little easier to follow. The names of those
        # methods were chosen so their (case independent) sorted order matched the
        # order that they're called. However, no matter how the initialization code
        # is organized, it's still difficult to follow.
        #
        # NOTE - the good news is, if you're willing to believe this stuff works, you
        # probably can skip all the initialization, return to main(), and still follow
        # the rest of the program.
        #

        cls.initialize1_fields()
        cls.initialize2_field_widths()
        cls.initialize3_layout()
        cls.initialize4_maps()
        cls.initialize5_attributes()

    @classmethod
    def initialize1_fields(cls) -> None:
        #
        # The main job in this method is to check the output styles for the ADDR, BYTE,
        # and TEXT fields that are set after the command line options are processed and
        # use them to initialize all other fields that depend on the selected style.
        #
        # Bits set in DUMP_field_flags represent the fields that will be printed in the
        # dump. All three fields are enabled when we start. Fields that are "EMPTY" will
        # have their flag bits cleared and when this method returns the flag bits set in
        # DUMP_field_flags represent the fields that are included in the dump.
        #

        cls.DUMP_field_flags = cls.ADDR_field_flag | cls.BYTE_field_flag | cls.TEXT_field_flag

        match cls.ADDR_output:
            case "DECIMAL":
                cls.ADDR_format_width = cls.ADDR_format_width if len(cls.ADDR_format_width) > 0 else cls.ADDR_format_width_default
                cls.ADDR_format = "%" + cls.ADDR_format_width + "d"
                cls.ADDR_digits = int(cls.ADDR_format_width)
                cls.ADDR_radix = 10
            case "EMPTY":
                cls.ADDR_format_width = "0"
                cls.ADDR_format = ""
                cls.ADDR_digits = 0
                cls.ADDR_radix = 0
                cls.DUMP_field_flags &= ~cls.ADDR_field_flag
            case "HEX-LOWER":
                cls.ADDR_format_width = cls.ADDR_format_width if len(cls.ADDR_format_width) > 0 else cls.ADDR_format_width_default
                cls.ADDR_format = "%" + cls.ADDR_format_width + "x"
                cls.ADDR_digits = int(cls.ADDR_format_width)
                cls.ADDR_radix = 16
            case "HEX-UPPER":
                cls.ADDR_format_width = cls.ADDR_format_width if len(cls.ADDR_format_width) > 0 else cls.ADDR_format_width_default
                cls.ADDR_format = "%" + cls.ADDR_format_width + "X"
                cls.ADDR_digits = int(cls.ADDR_format_width)
                cls.ADDR_radix = 16
            case "OCTAL":
                cls.ADDR_format_width = cls.ADDR_format_width if len(cls.ADDR_format_width) > 0 else cls.ADDR_format_width_default
                cls.ADDR_format = "%" + cls.ADDR_format_width + "o"
                cls.ADDR_digits = int(cls.ADDR_format_width)
                cls.ADDR_radix = 8
            case "XXD":
                cls.ADDR_output = "HEX-LOWER"
                cls.ADDR_format_width = cls.ADDR_format_width if len(cls.ADDR_format_width) > 0 else cls.ADDR_format_width_default_xxd
                cls.ADDR_format = "%" + cls.ADDR_format_width + "x"
                cls.ADDR_digits = int(cls.ADDR_format_width)
                cls.ADDR_radix = 16
            case _:
                cls.internal_error("address output", delimit(cls.ADDR_output), "has not been implemented")

        if cls.ADDR_format_width_limit > 0:
            if cls.ADDR_digits > cls.ADDR_format_width_limit:
                cls.user_error("address width", delimit(cls.ADDR_format_width), "exceeds the internal limit of", delimit(str(cls.ADDR_format_width_limit)))

        #
        # Unlike the bash version, counting the extra characters that print in the ADDR
        # field of the dump is trivial and locale independent, but only because we made
        # sure (in the option handling code) that all those characters are printable.
        #

        cls.ADDR_prefix_size = len(cls.ADDR_prefix)
        cls.ADDR_suffix_size = len(cls.ADDR_suffix)
        cls.ADDR_field_separator_size = len(cls.ADDR_field_separator)
        cls.ADDR_padding = "0" if cls.ADDR_format_width.startswith("0") else " "

        match cls.TEXT_output:
            case "ASCII":
                cls.TEXT_map = "ASCII_TEXT_MAP"
                cls.TEXT_chars_per_octet = 1
                cls.TEXT_unexpanded_string = "?"
            case "CARET":
                cls.TEXT_map = "CARET_TEXT_MAP"
                cls.TEXT_chars_per_octet = 2
                cls.TEXT_unexpanded_string = "??"
            case "CARET_ESCAPE":
                cls.TEXT_map = "CARET_ESCAPE_TEXT_MAP"
                cls.TEXT_chars_per_octet = 2
                cls.TEXT_unexpanded_string = "??"
            case "EMPTY":
                cls.TEXT_map = ""
                cls.TEXT_chars_per_octet = 0
                cls.TEXT_unexpanded_string = ""
                cls.BYTE_field_separator = ""
                cls.DUMP_layout = cls.DUMP_layout_default
                cls.DUMP_field_flags &= ~cls.TEXT_field_flag
            case "UNICODE":
                cls.TEXT_map = "UNICODE_TEXT_MAP"
                cls.TEXT_chars_per_octet = 1
                cls.TEXT_unexpanded_string = "?"
            case "XXD":
                cls.TEXT_output = "ASCII"
                cls.TEXT_map = "ASCII_TEXT_MAP"
                cls.TEXT_chars_per_octet = 1
                cls.TEXT_unexpanded_string = "?"
            case _:
                cls.internal_error("text output", delimit(cls.TEXT_output), "has not been implemented")

        #
        # Unlike the bash version, counting the extra characters that print in the TEXT
        # field of the dump is trivial and locale independent, but only because we made
        # sure (in the option handling code) that all those characters are printable.
        #

        cls.TEXT_prefix_size = len(cls.TEXT_prefix)
        cls.TEXT_suffix_size = len(cls.TEXT_suffix)
        cls.TEXT_separator_size = len(cls.TEXT_separator)

        if len(cls.TEXT_map) > 0:
            if not hasattr(cls, cls.TEXT_map):
                cls.internal_error(delimit(cls.TEXT_map), "is not recognized as a TEXT field mapping array name")

        match cls.BYTE_output:
            case "BINARY":
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 8
            case "DECIMAL":
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 3
            case "EMPTY":
                if cls.TEXT_output != "EMPTY":
                    cls.BYTE_map = ""
                    cls.BYTE_digits_per_octet = 0
                    cls.DUMP_layout = cls.DUMP_layout_default
                    cls.DUMP_field_flags &= ~cls.BYTE_field_flag
                else:
                    cls.user_error("byte and text fields can't both be empty")
            case "HEX-LOWER":
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 2
            case "HEX-UPPER":
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 2
            case "OCTAL":
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 3
            case "XXD":
                cls.BYTE_output = "HEX-LOWER"
                cls.BYTE_map = "byte_map"
                cls.BYTE_digits_per_octet = 2
            case _:
                cls.internal_error("byte output", delimit(cls.BYTE_output), "has not been implemented")

        if len(cls.BYTE_map) > 0:
            if not hasattr(cls, cls.BYTE_map):
                cls.internal_error(delimit(cls.BYTE_map), "is not recognized as a BYTE field mapping array name")

        #
        # Unlike the bash version, counting the extra characters that print in the BYTE
        # field of the dump is trivial and locale independent, but only because we made
        # sure (in the option handling code) that all those characters are printable.
        #

        cls.BYTE_prefix_size = len(cls.BYTE_prefix)
        cls.BYTE_suffix_size = len(cls.BYTE_suffix)
        cls.BYTE_separator_size = len(cls.BYTE_separator)

        if cls.DUMP_record_length_limit > 0:
            if cls.DUMP_record_length > cls.DUMP_record_length_limit:
                cls.user_error("requested record length", delimit(str(cls.DUMP_record_length)), "exceeds the internal buffer limit of", delimit(str(cls.DUMP_record_length_limit)), "bytes")

    @classmethod
    def initialize2_field_widths(cls) -> None:
        #
        # All we use BYTE_field_width for is to decide whether the BYTE field in the
        # dump's last record needs space padding, after the final byte, to make sure
        # its TEXT field starts in the correct column. It's only used in dump_all(),
        # so that's where to look for more details.
        #
        # NOTE - even though the value stored in BYTE_field_width is correct, all we
        # really care about in this class is whether it's zero or not. A zero value
        # means padding isn't needed, which will happen when the BYTE or TEXT field
        # is empty, we're doing a single record or narrow dump, or there aren't any
        # missing bytes in the last record.
        #

        if cls.DUMP_record_length > 0:
            if cls.BYTE_output == "EMPTY" or cls.TEXT_output == "EMPTY" or cls.DUMP_layout == "NARROW":
                cls.BYTE_field_width = 0
            else:
                cls.BYTE_field_width = cls.DUMP_record_length * (cls.BYTE_digits_per_octet + cls.BYTE_separator_size) - cls.BYTE_separator_size
        else:
            cls.BYTE_field_width = 0

    @classmethod
    def initialize3_layout(cls) -> None:
        padding: int

        #
        # Different "layouts" give the user a little control over the arrangement of
        # each record's ADDR, BYTE, and TEXT fields. The currently supported layouts
        # are named "WIDE" and "NARROW". There are other possibilites, but these two
        # are easy to describe and feel like they should be more than sufficent. They
        # can be requested on the command line using the --wide or --narrow options.
        #
        # WIDE is the default layout and it generally resembles the way xxd organizes
        # its output - the ADDR, BYTE, and TEXT fields are printed next to each other,
        # and in that order, on the same line.
        #
        # The NARROW layout is harder and needs lots of subtle calculations to make
        # sure everything gets lined up properly. Basically NARROW layout prints the
        # ADDR and BYTE fields next to each other on the same line. The TEXT field is
        # printed by itself on the next line and what we have to do here is make sure
        # each character in the TEXT field is printed directly below the appropriate
        # byte in the BYTE field. The calculations are painful, so they've been split
        # into small steps that hopefully will be little easier to follow.
        #

        if cls.DUMP_layout == "NARROW":
            #
            # In this case, each TEXT field is supposed to be printed directly below
            # the corresponding BYTE field. Lots of adjustments will be required, but
            # the first step is make sure the TEXT and BYTE fields print on separate
            # lines by assigning a newline to the string that separates the BYTE field
            # from the TEXT field.
            #

            cls.BYTE_field_separator = "\n"

            #
            # Figure out the number of spaces that need to be appended to the TEXT or
            # BYTE field indents to make the first byte and first character end up in
            # the same "column". The positioning of individual text characters within
            # the column will be addressed separately.
            #

            padding = cls.BYTE_prefix_size - cls.TEXT_prefix_size
            if padding > 0:
                cls.TEXT_indent = cls.TEXT_indent + f"{'':>{padding}}"
            elif padding < 0:
                cls.BYTE_indent = cls.BYTE_indent + f"{'':>{-padding}}"

            #
            # Next, modify the separation between individual bytes in the BYTE field
            # or characters in the TEXT field so they all can be lined up vertically
            # when they're printed on separate lines.
            #

            padding = cls.BYTE_digits_per_octet - cls.TEXT_chars_per_octet + cls.BYTE_separator_size - cls.TEXT_separator_size
            if padding > 0:
                cls.TEXT_separator = cls.TEXT_separator + f"{'':>{padding}}"
                cls.TEXT_separator_size = len(cls.TEXT_separator)
            elif padding < 0:
                cls.BYTE_separator = cls.BYTE_separator + f"{'':>{-padding}}"
                cls.BYTE_separator_size = len(cls.BYTE_separator)

            #
            # Adjust the TEXT field prefix by appending the number of spaces needed
            # to make sure the first character lines up right adjusted and directly
            # below the first displayed byte.
            #

            padding = cls.BYTE_digits_per_octet - cls.TEXT_chars_per_octet
            if padding > 0:
                cls.TEXT_prefix = cls.TEXT_prefix + f"{'':>{padding}}"
                cls.TEXT_prefix_size = len(cls.TEXT_prefix)
            elif padding < 0:
                cls.internal_error("chars per octet exceeds digits per octet")

            #
            # If there's an address, adjust the TEXT field indent so all characters
            # line up vertically with the appropriate BYTE field bytes.
            #

            if cls.ADDR_output != "EMPTY":
                padding = cls.ADDR_prefix_size + cls.ADDR_digits + cls.ADDR_suffix_size + cls.ADDR_field_separator_size
                if padding > 0:
                    cls.TEXT_indent = cls.TEXT_indent + f"{'':>{padding}}"

        elif cls.DUMP_layout != "WIDE":
            cls.internal_error("layout", delimit(cls.DUMP_layout), "has not been implemented")

    @classmethod
    def initialize4_maps(cls) -> None:
        codepoint: int
        element: str
        encoding: str
        index: int
        manager: RegexManager

        #
        # Makes sure the BYTE and TEXT field mapping arrays referenced by BYTE_map and
        # TEXT_map exist. The BYTE field mapping array that's used to generate the dump
        # is built here, very much like what's done in the bash version of bytedump. The
        # TEXT field mapping array must already exist, but this is where we make sure
        # that every byte in the dump will be represented in the TEXT field by characters
        # that are compatible with the user's locale. It's something that every bytedump
        # implementation tries to address, but it's low level behavior that only happens
        # at runtime and has to be solved using whatever tools the underlying programming
        # language provides.
        #
        # NOTE - if you always assume UTF-8 character encoding than the issues disappear,
        # but if not you can force an encoding, like 8859-15, to illustrate the problems.
        # BYTE field mapping arrays only contain ASCII strings, so they never need to be
        # checked (in every version of bytedump).
        #
        # NOTE - there's more work to do for the TEXT field mapping array than you might
        # expect. Take a close look at the TEXT field mapping array initializers and you
        # hopefully will notice that occurrences of "\\uXXXX" in string literals really
        # aren't Unicode escape sequences. Instead, what happens when the string literal
        # is processed is that the two backslashes are replaced by a single backslash and
        # immediately followed by the 'u' and the four hex digits. In other words if you
        # see something like
        #
        #     "\\u00B6"
        #
        # at an index in a TEXT field mapping array's initializer, this method would see
        # the string
        #
        #     "\u00B6"
        #
        # at that same index. In fact, all we need here are the hex digits, so the "\\u"
        # prefix really is unnecessary overhead.
        #

        if cls.BYTE_map is not None and len(cls.BYTE_map) > 0:
            #
            # We now follow the bash version's approach and only build the BYTE field
            # mapping array that we really need. No compiler to do the work once for
            # us, so the bash approach seems like the right model to follow and Python
            # makes that easy.
            #
            match cls.BYTE_output:
                case "BINARY":
                    cls.byte_map = [f"{i:08b}" for i in range(256)]
                case "DECIMAL":
                    cls.byte_map = [f"{i:>3}" for i in range(256)]
                case "HEX-LOWER":
                    cls.byte_map = [f"{i:02x}" for i in range(256)]
                case "HEX-UPPER":
                    cls.byte_map = [f"{i:02X}" for i in range(256)]
                case "OCTAL":
                    cls.byte_map = [f"{i:03o}" for i in range(256)]
                case _:
                    cls.internal_error("builder for base", delimit(cls.BYTE_output), "map has not been implemented")
        else:
            cls.byte_map = None

        if cls.TEXT_map is not None and len(cls.TEXT_map) > 0:
            cls.text_map = getattr(cls, cls.TEXT_map, None)
            if cls.text_map is not None:
                manager = RegexManager()
                encoding = sys.stdout.encoding or "utf-8"
                #
                # Loop uses a regular expression to look through the selected mapping array
                # for the hex digits that represent Unicode code points that still need to
                # be expanded. We do it here, rather than in the text field mapping array's
                # initializer, so we can catch the exception that's thrown whenever there's
                # an encoding problem and try do something reasonable.
                #
                for index in range(len(cls.text_map)):
                    element = cls.text_map[index]
                    if manager.matched(element, r"^(.*)(\\u([0123456789abcdefABCDEF]{4}))$"):
                        codepoint = int(manager.cached_groups[3], 16)
                        try:
                            chr(codepoint).encode(encoding)
                            cls.text_map[index] = manager.cached_groups[1] + chr(codepoint)
                        except UnicodeEncodeError:
                            cls.text_map[index] = cls.TEXT_unexpanded_string
            else:
                cls.internal_error(delimit(cls.TEXT_map), "is not a recognized text mapping array name")
        else:
            cls.text_map = None

    @classmethod
    def initialize5_attributes(cls) -> None:
        byte_table: list[str | None]
        field: str
        field_map: list[str] | None
        index: int
        key: str
        last: int
        layer: str
        manager: RegexManager
        prefix: str
        suffix: str

        #
        # Applies attributes that were selected by command line options to the active
        # TEXT and BYTE field mapping arrays.
        #

        manager = RegexManager()
        last = last_encoded_byte()

        for key in cls.attribute_tables.registered_keys:
            byte_table = cls.attribute_tables.get(key)
            if byte_table is not None:
                if manager.matched(key, "^(BYTE|TEXT)_(.+)$"):
                    field = manager.cached_groups[1]
                    layer = manager.cached_groups[2]

                    field_map = cls.byte_map if field == "BYTE" else cls.text_map

                    if field_map is not None:
                        suffix = cls.ANSI_ESCAPE.get("RESET.attributes", "")
                        for index in range(len(byte_table)):
                            if index <= last:
                                if byte_table[index] is not None and index < len(field_map):
                                    prefix = cls.ANSI_ESCAPE.get(layer + "." + byte_table[index], "")
                                    if len(prefix) > 0:
                                        field_map[index] = prefix + field_map[index] + suffix

    @classmethod
    def main(cls, args: list[str]) -> None:
        #
        # This method runs the program, basically by just calling the other methods that
        # do the real work.
        #

        try:
            cls.setup()
            cls.options(args)
            cls.initialize()
            cls.debug()
            cls.arguments(args[cls.arguments_consumed:])
        except Terminator.ExitException as e:
            message = e.get_message()
            if message is not None and len(message) > 0:
                sys.stderr.write(message + "\n")

            if e.get_status() != 0:
                sys.exit(e.get_status())

    @classmethod
    def options(cls, args: list[str]) -> None:
        arg: str
        attribute: str
        done: bool
        format_width: str
        length: str
        manager: RegexManager
        mode: str
        next_idx: int
        optarg: str
        selector: str
        style: str
        target: str

        #
        # A long, but straightforward method that uses RegexManager to process command line
        # options. Everything was designed so this method would "resemble" the way options
        # were handled in the Java and bash implementations of bytedump, and the RegexManager
        # class, which is defined later in this file, is a fundamental part of the solution
        # to that puzzle.
        #
        # Just like the bash version, main() needs to know how many arguments were consumed as
        # options. That number is stored in the arguments_consumed class variable right before
        # this method returns, but only because that approach "resembles" how the bash version
        # does it. There are many other ways this could be handled in a Python program.
        #
        # NOTE - the options that set prefixes, separators, and suffixes let the user provide
        # strings that will appear in the dump we generate. That means the arguments of those
        # options are checked using a character class that accepts any character that the user
        # would consider printable.
        #

        manager = RegexManager()
        done = False
        next_idx = 0

        while next_idx < len(args):
            arg = args[next_idx]

            if manager.matched(arg, "^(--[^=-][^=]*=)(.*)$"):
                target = manager.cached_groups[1]
                optarg = manager.cached_groups[2]
            elif manager.matched(arg, "^(--[^=-][^=]*)$"):
                target = manager.cached_groups[1]
                optarg = ""
            else:
                target = arg
                optarg = ""

            match target:
                case "--addr=":
                    if manager.matched(optarg, "^[ \\t]*(decimal|empty|hex|HEX|octal|xxd)[ \\t]*([:][ \\t]*([0]?[1-9][0-9]*)[ \\t]*)?$"):
                        style = manager.cached_groups[1]
                        format_width = manager.cached_groups[3]

                        match style:
                            case "decimal":
                                style = "DECIMAL"
                            case "empty":
                                style = "EMPTY"
                            case "hex":
                                style = "HEX-LOWER"
                            case "HEX":
                                style = "HEX-UPPER"
                            case "octal":
                                style = "OCTAL"
                            case "xxd":
                                style = "XXD"
                            case _:
                                cls.internal_error("option", delimit(arg), "has not been completely implemented")

                        cls.ADDR_output = style
                        if format_width is not None:
                            cls.ADDR_format_width = format_width
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--addr-prefix=":
                    if printable_user_string(optarg):
                        cls.ADDR_prefix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--addr-suffix=":
                    if printable_user_string(optarg):
                        cls.ADDR_suffix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_BACKGROUND"))
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--byte=":
                    if manager.matched(optarg, "^[ \\t]*(binary|decimal|empty|hex|HEX|octal|xxd)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$"):
                        style = manager.cached_groups[1]
                        length = manager.cached_groups[3]

                        match style:
                            case "binary":
                                style = "BINARY"
                            case "decimal":
                                style = "DECIMAL"
                            case "empty":
                                style = "EMPTY"
                            case "hex":
                                style = "HEX-LOWER"
                            case "HEX":
                                style = "HEX-UPPER"
                            case "octal":
                                style = "OCTAL"
                            case "xxd":
                                style = "XXD"
                            case _:
                                cls.internal_error("option", delimit(arg), "has not been completely implemented")

                        cls.BYTE_output = style
                        if length is not None:
                            #
                            # We assume Python 3, so ints don't impose an upper bound on length
                            # that we can check. In addition, length was successfully matched by
                            # a regular expression that only recognized decimal, hex, and octal
                            # numbers, so int() should be able to handle any length we give it.
                            #
                            cls.DUMP_record_length = int(length, 0)
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--byte-background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--byte-foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--byte-prefix=":
                    if printable_user_string(optarg):
                        cls.BYTE_prefix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--byte-separator=":
                    if printable_user_string(optarg):
                        cls.BYTE_separator = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--byte-suffix=":
                    if printable_user_string(optarg):
                        cls.BYTE_suffix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--copyright":
                    print(cls.PROGRAM_COPYRIGHT)
                    Terminator.terminate()

                case "--debug=":
                    for mode in optarg.split(","):
                        mode = mode.strip()
                        match mode:
                            case "background":
                                cls.DEBUG_background = True
                            case "bytemap":
                                cls.DEBUG_bytemap = True
                            case "foreground":
                                cls.DEBUG_foreground = True
                            case "settings":
                                cls.DEBUG_settings = True
                            case "textmap":
                                cls.DEBUG_textmap = True
                            case _:
                                if len(mode) > 0:
                                    cls.user_error("debugging mode", delimit(mode), "in option", delimit(arg), "is not recognized")

                case "--foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_FOREGROUND"))
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--help":
                    cls.help()
                    Terminator.terminate()

                case "--length=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_record_length = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--length-limit=":         # undocumented option
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_record_length_limit = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--license":
                    print(cls.PROGRAM_LICENSE)
                    Terminator.terminate()

                case "--narrow":
                    cls.DUMP_layout = "NARROW"

                case "--read=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_input_read = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--spacing=":
                    if manager.matched(optarg, "^[ \\t]*(1|single|2|double|3|triple)[ \\t]*$"):
                        match manager.cached_groups[1]:
                            case "1" | "single":
                                cls.DUMP_record_separator = "\n"
                            case "2" | "double":
                                cls.DUMP_record_separator = "\n\n"
                            case "3" | "triple":
                                cls.DUMP_record_separator = "\n\n\n"
                            case _:
                                cls.internal_error("option", delimit(arg), "has not been completely implemented")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--start=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$"):
                        cls.DUMP_input_start = int(manager.cached_groups[1], 0)
                        if manager.cached_groups[3] is not None:
                            cls.DUMP_output_start = int(manager.cached_groups[3], 0)
                        else:
                            cls.DUMP_output_start = cls.DUMP_input_start
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--text=":
                    if manager.matched(optarg, "^[ \\t]*(ascii|caret|empty|escape|unicode|xxd)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$"):
                        style = manager.cached_groups[1]
                        length = manager.cached_groups[3]

                        match style:
                            case "ascii":
                                style = "ASCII"
                            case "caret":
                                style = "CARET"
                            case "empty":
                                style = "EMPTY"
                            case "escape":
                                style = "CARET_ESCAPE"
                            case "unicode":
                                style = "UNICODE"
                            case "xxd":
                                style = "XXD"
                            case _:
                                cls.internal_error("option", delimit(arg), "has not been completely implemented")

                        cls.TEXT_output = style
                        if length is not None:
                            #
                            # We assume Python 3, so ints don't impose an upper bound on length
                            # that we can check. In addition, length was successfully matched by
                            # a regular expression that only recognized decimal, hex, and octal
                            # numbers, so int() should be able to handle any length we give it.
                            #
                            cls.DUMP_record_length = int(length, 0)
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--text-background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--text-foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "is not recognized")

                case "--text-prefix=":
                    if printable_user_string(optarg):
                        cls.TEXT_prefix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--text-suffix=":
                    if printable_user_string(optarg):
                        cls.TEXT_suffix = optarg
                    else:
                        cls.user_error("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters")

                case "--version":
                    print(cls.PROGRAM_VERSION)
                    Terminator.terminate()

                case "--wide":
                    cls.DUMP_layout = "WIDE"

                case "-":
                    done = True

                case "--":
                    done = True
                    next_idx += 1

                case _:
                    done = True
                    if target.startswith("-"):
                        cls.user_error("invalid option", delimit(arg))

            if done:
                break

            next_idx += 1

        cls.arguments_consumed = next_idx

    @classmethod
    def setup(cls) -> None:
        #
        # This is where initialization that needs to happen before the command line
        # options are processed can be done. The initialization of attribute_tables
        # uses the AttributeTables constructor, so it's done here just to make sure
        # it doesn't depend on exactly where that class is defined.
        #

        cls.attribute_tables = AttributeTables(
            "BYTE_BACKGROUND", "BYTE_FOREGROUND",
            "TEXT_BACKGROUND", "TEXT_FOREGROUND"
        )

    ###################################
    #
    # ByteDump - Error Methods
    #
    ###################################

    @classmethod
    def internal_error(cls, *args: str) -> None:
        Terminator.error_handler(
            "-prefix=" + cls.PROGRAM_NAME,
            "-tag=InternalError",
            "-info=location",
            "+exit",
            "+frame",
            "--",
            " ".join(args)
        )

    @classmethod
    def python_error(cls, *args: str) -> None:
        Terminator.error_handler(
            "-prefix=" + cls.PROGRAM_NAME,
            "-tag=PythonError",
            "-info=location",
            "+exit",
            "+frame",
            "--",
            " ".join(args)
        )

    @classmethod
    def user_error(cls, *args: str) -> None:
        Terminator.error_handler(
            "-prefix=" + cls.PROGRAM_NAME,
            "-tag=Error",
            "-info",
            "+exit",
            "+frame",
            "--",
            " ".join(args)
        )

###################################
#
# Helper Functions
#
###################################

def delimit(arg: Any) -> str:
    #
    # This is really only used to maintain some resemblance to the Java version, which
    # needed help dealing with nulls.
    #

    return "\"" + " ".join(arg) + "\"" if isinstance(arg, list) else f"\"{str(arg)}\""

def last_encoded_byte() -> int:
    #
    # Decided to always return 255, at least until I can remember exactly why the Java
    # and bash versions thought 127 would sometimes be appropriate. Probably will do
    # the same thing in the other bytedump versions.
    #

    return 255

def printable_user_string(arg: str) -> bool:
    #
    # Just used to make sure that all of the characters in the strings that a user can
    # "add" to our dump using command line options (e.g., --addr-suffix) are printable
    # characters. It's important, because we count characters in those strings to make
    # sure everything in the dump lines up vertically. The bash and Java versions were
    # able to do this by combining locales with appropriate regular expressions, but
    # I'm not sure how to make that approach work in Python. Anyway, what's done here
    # seems to be sufficient.
    #

    if arg.isprintable():
        try:
            #
            # I think this part works - the Python UTF-8 Mode documentation seems to
            # imply that issues with locale.getpreferredencoding() are only enabled
            # (at startup) when LC_CTYPE is C or POSIX.
            #
            encoding = locale.getpreferredencoding(False)
            arg.encode(encoding)
            return True
        except UnicodeEncodeError:
            pass
    return False

###################################
#
# AttributeTables - Helper Class
#
###################################

class AttributeTables(dict):
    #
    # This class tries to replicate how the Java implementation manages attributes
    # (like colors) that can be assigned by options and later applied to the dump.
    # It's called in options() and used by byte_selector() to associate attributes
    # with individual bytes.
    #
    # NOTE - there likely are better approaches, but this is sufficient. The main
    # reason for using this stuff is to help simplify the management of attributes
    # during option processing - take a look at the comments about attributes and
    # options in the bash and Java implementations if you want more details.
    #

    TABLE_SIZE: int = 256               # one attribute slot for each byte

    def __init__(self, *keys: str):
        super().__init__()
        self.registered_keys = set()

        if len(keys) > 0:
            for key in keys:
                if key is not None:
                    self[key] = None
                    self.registered_keys.add(key)
                else:
                    raise ValueError("null keys are not allowed")
        else:
            raise ValueError("constructor requires at least one argument")

    def dump_table(self, key: str, prefix: str) -> None:
        #
        # This method reproduces the "debugging" output that the original bash version
        # of bytedump produced when it was asked to display "background" or "foreground"
        # attributes that command line options assigned to individual bytes displayed in
        # the dump's BYTE or TEXT fields. Occasionally helpful, but it has nothing to do
        # with the actual generation of the dump.
        #

        table = self.get(key)
        if table is not None:
            count = 0
            prefix = prefix if prefix is not None else ""
            elements = ""
            separator = ""

            for index in range(len(table)):
                value = table[index]
                if value is not None:
                    # Formatting logic mirroring Java's String.format
                    # "%s%s  %5s=%s"
                    elements += f"{separator}{prefix}  {'[' + str(index) + ']':>5}=\"{value}\""
                    separator = "\n"
                    count += 1

            if count > 0:
                sys.stderr.write(f"{prefix}{key}[{count}]:\n")
                sys.stderr.write(f"{elements}\n")
                sys.stderr.write("\n")

    def get_table(self, key: str) -> list[str | None]:
        #
        # Returns the table that is (or soon will be) associated with key, but only if
        # key is in registered_keys. The table is created and added to this dict if it's
        # not there yet, which should only happen on the first request for key's table.
        #

        if key in self.registered_keys:
            if key is not None:
                table = self.get(key)
                if table is None:
                    table = [None] * self.TABLE_SIZE
                    self[key] = table
            else:
                raise ValueError("Key cannot be None")
        else:
            raise ValueError(f"{key} is not a key that was registered by the constructor.")

        return table

###################################
#
# RegexManager - Helper Class
#
###################################

class RegexManager:
    #
    # Simple class that supports some regular expression methods that can be used to
    # replicate how regular expressions are used in the Java bytedump implemenation.
    # Caching groups recognized by matched() means the program doesn't need to call
    # matched_groups() to get them.
    #

    cached_groups: list[str] = None

    def matched(self, text: str, regex: str) -> bool:
        #
        # This currently is the only method that caches matched groups. It helped us
        # simplify some of the regex matching code (without using the := assignment
        # operator).
        #

        self.cached_groups = self.matched_groups(text, regex)
        return self.cached_groups is not None

    def matched_group(self, group_index: int, text: str, regex: str) -> str | None:
        #
        # No group caching by this method, at least right now. Not 100% convinced it's
        # the right approach, but it's also not unreasonable because the RegexManager
        # class was only designed to be be used by the ByteDump class.
        #

        groups = self.matched_groups(text, regex)
        return groups[group_index] if groups and group_index < len(groups) else None

    def matched_groups(self, text: str, regex: str) -> list[str] | None:
        #
        # No group caching by this method, at least right now. Not 100% convinced it's
        # the right approach, but it's also not unreasonable because the RegexManager
        # class was only designed to be be used by the ByteDump class.
        #

        groups = None
        if text is not None and regex is not None:
            match = re.search(regex, text)
            if match:
                groups = [match.group(0)] + list(match.groups())
        return groups

    def matches(self, text: str, regex: str) -> bool:
        #
        # Same return value as the matched() method, but doesn't cache matched groups
        # so there's less overhead and it will run a little faster. Currently unused,
        #
        # NOTE - currently unused, but it's included for completeness and because I
        # may include the group caching stuff in the Java version of RegexManager.
        #

        if text is not None and regex is not None:
            return re.search(regex, text) is not None
        else:
            return False

###################################
#
# Terminator - Helper Class
#
###################################

class Terminator:
    #
    # This class tries to replicate most of the capabilities built into the Terminator
    # class that's included in the Java version of bytedump. The Java class was written
    # so it could be used by other Java applications, but that's definitely not the goal
    # here. Instead, all this class is supposed to do is to provide a way to duplicate
    # the error method calls, the error messages, and the way the error handling ends up
    # in the main() method.
    #

    # Constants used in message_formatter to select info
    CALLER_INFO: str = "CALLER"
    LINE_INFO: str = "LINE"
    LOCATION_INFO: str = "LOCATION"
    METHOD_INFO: str = "METHOD"
    SOURCE_INFO: str = "SOURCE"

    # Keys for stack frame info
    FRAME_LINE: str = "LINE"
    FRAME_METHOD: str = "METHOD"
    FRAME_SOURCE: str = "SOURCE"

    UNKNOWN_FILE_TAG: str = "File unknown"
    UNKNOWN_LINE_TAG: str = "unknown"

    DEFAULT_EXIT_STATUS: int = 1

    ###################################
    #
    # Terminator Methods
    #
    ###################################

    @classmethod
    def error_handler(cls, *args: str) -> str:
        arguments: list[str]
        manager: RegexManager
        done: bool
        should_exit: bool
        arg: str
        message: str
        optarg: str
        opttag: str
        target: str
        status: int
        index: int

        should_exit = True
        status = cls.DEFAULT_EXIT_STATUS

        arguments = []
        arguments.append("-tag=Error")
        arguments.append("-info=location")

        manager = RegexManager()
        done = False
        index = 0

        # Argument parsing loop mirroring Java
        while index < len(args):
            arg = args[index]
            if manager.matched(arg, "^(([+-])[^=+-][^=]*)(([=])(.*))?$"):
                target = manager.cached_groups[1]
                opttag = manager.cached_groups[2]
                optarg = manager.cached_groups[5]
            else:
                target = arg
                opttag = ""
                optarg = ""

            match target:
                case "+exit":
                    should_exit = True
                case "-exit":
                    should_exit = False
                case "-status":
                    try:
                        status = int(optarg)
                    except ValueError:
                        pass
                case "--":
                    done = True
                    index += 1
                case _:
                    if opttag == "+" or opttag == "-":
                        arguments.append(arg)
                    else:
                        done = True

            if done:
                break

            index += 1

        # Hand off remaining args
        arguments.append("+frame")
        arguments.append("--")
        arguments.append(" ".join(args[index:]))

        message = cls.message_formatter(arguments)

        if should_exit:
            cls.terminate(message, None, status)

        return message

    @classmethod
    def terminate(cls, message: str | None = "", cause: BaseException | None = None,
                  status: int = DEFAULT_EXIT_STATUS) -> None:

        #
        # Gemini's original Python version of this method set the default message to None.
        # However, apparently somewhere behind the scenes that None message was translated
        # to the string "None", which ended up as the message that main() printed whenever
        # this method is called with no arguments.
        #
        # Changing the default message to the empty string (i.e., "") fixed that behavior,
        # but only because main() explicitly ignores all messages that are None or empty
        # strings. After that I decided not to spend more time trying to track down where
        # the translation of None to "None" happened.
        #

        raise Terminator.ExitException(message, cause, status)

    @classmethod
    def message_formatter(cls, args: list[str]) -> str:
        caller: dict[str, str]
        manager: RegexManager
        groups: list[str] | None
        done: bool
        arg: str
        message: str | None
        optarg: str
        opttag: str
        target: str
        info: str | None
        prefix: str | None
        suffix: str | None
        tag: str | None
        frame_offset: int
        index: int

        message = None
        info = None
        prefix = None
        suffix = None
        tag = None
        frame_offset = 1

        manager = RegexManager()
        done = False
        index = 0

        while index < len(args):
            arg = args[index]
            groups = manager.matched_groups(arg, "^(([+-])[^=+-][^=]*)(([=])(.*))?$")
            if groups is not None:
                target = groups[1]
                opttag = groups[2]
                optarg = groups[5]
            else:
                target = arg
                opttag = ""
                optarg = ""

            match target:
                case "+frame":
                    frame_offset += 1
                case "-frame":
                    frame_offset = 0
                case "-info":
                    info = optarg
                case "-prefix":
                    prefix = optarg
                case "-suffix":
                    suffix = optarg
                case "-tag":
                    tag = optarg
                case "--":
                    done = True
                    index += 1
                case _:
                    if opttag != "+" and opttag != "-":
                        done = True

            if done:
                break

            index += 1

        if index < len(args):
            message = " ".join(args[index:])

        if info is not None:
            # Python Stack Inspection
            # stack[0] is current, stack[1] is caller of message_formatter, etc.
            # Java default was frame=1 (caller of messageFormatter).
            # We need to account for Python's stack structure.
            # 0: message_formatter
            # 1: error_handler (usually)
            # 2: The actual caller we want

            stack = inspect.stack()

            if frame_offset < len(stack):
                frame_info = stack[frame_offset]
                # frame_info is a FrameInfo object or tuple

                caller = {}
                line_no = frame_info.lineno
                caller[cls.FRAME_LINE] = str(line_no) if line_no >= 0 else cls.UNKNOWN_LINE_TAG
                caller[cls.FRAME_METHOD] = frame_info.function

                # frame_info.filename gives full path, Java often gives just file name.
                # using os.path.basename to match typical Java behavior
                fname = frame_info.filename
                caller[cls.FRAME_SOURCE] = os.path.basename(fname) if fname else cls.UNKNOWN_FILE_TAG

                for token in info.split(","):
                    token_upper = token.strip().upper()

                    # Logic: tag = String.join("", tag, "] [", ...)
                    # Check for null tag first to avoid "None] ["
                    current_tag = tag if tag is not None else ""

                    # NOTE: Python string join logic slightly different than Java's String.join with delimiter
                    # Java: String.join("", tag, "] [", val) -> tag + "] [" + val

                    # We need to handle the initial join if tag is empty?
                    # Java code: tag = String.join("", tag, "] [", ...)
                    # If tag was "Error", it becomes "Error] [LOCATION..."

                    part = ""
                    if token_upper == cls.CALLER_INFO:
                        part = f"{caller[cls.FRAME_SOURCE]}; {caller[cls.FRAME_METHOD]}; Line {caller[cls.FRAME_LINE]}"
                    elif token_upper == cls.LINE_INFO:
                        part = f"Line {caller[cls.FRAME_LINE]}"
                    elif token_upper == cls.LOCATION_INFO:
                        part = f"{caller[cls.FRAME_SOURCE]}; Line {caller[cls.FRAME_LINE]}"
                    elif token_upper == cls.METHOD_INFO:
                        part = caller[cls.FRAME_METHOD]
                    elif token_upper == cls.SOURCE_INFO:
                        part = caller[cls.FRAME_SOURCE]

                    if len(part) > 0:
                        tag = f"{current_tag}] [{part}"

        # Final Assembly
        result = ""
        if prefix is not None and len(prefix) > 0:
            result += prefix + ": "
        if message is not None and len(message) > 0:
            result += message + " "
        if tag is not None and len(tag) > 0:
            result += "[" + tag + "]"
        if suffix is not None and len(suffix) > 0:
            result += suffix

        return result

    ###################################
    #
    # Terminator.ExitException
    #
    ###################################

    class ExitException(RuntimeError):
        def __init__(self, message: str | None = None, cause: BaseException | None = None, status: int = 1):
            super().__init__(message)
            self.status = status
            if cause:
                self.__cause__ = cause

        def get_status(self) -> int:
            return self.status

        def get_message(self) -> str:
            return str(self)

###################################
#
# Documentation
#
###################################

bytedump_help = """
 SYNOPSIS
 ========

 bytedump-python [OPTIONS] [FILE|-]

 DESCRIPTION
 ===========

 A program that generates a dump of the bytes in FILE, which must be a readable file
 that's not a directory. Standard input is read if the argument is missing or equal
 to '-'.

 This is the Python implementation of that program. The initial version was written
 by Gemini 3.0 Pro in a single chat that was an experiment that happened in December
 2025. The source code that Gemini produced and the instructions that it was asked
 to follow were added to the GitHub repository

     https://github.com/rich-drechsler/bytedump

 on 12/23/25 and for now all changes made to it can be tracked in that repository.

 OPTIONS
 =======

 Options are processed in the order they appear on the command line and options that
 are processed later take precedence. Option processing continues until there are no
 more arguments that start with a '-' character. The option '--', which is otherwise
 ignored, can be used to mark the end of the options. The argument '-', which always
 stands for standard input, also ends option processing.

 The documented options are:

     --addr=<style>
     --addr=<style>:<width>
         The <style> controls how addresses are displayed. It must be one of the
         case-dependent strings in the list:

             decimal - addresses are displayed in decimal (width=6)
                 hex - addresses are displayed in lowercase hex (width=6)
                 HEX - addresses are displayed in uppercase hex (width=6)
               octal - addresses are displayed in octal (width=6)
                 xxd - addresses are displayed in lowercase hex (width=08)

               empty - address fields are all empty

         The <width> that can be set using this option is the minimum <width> of
         the field, in digits, that's allocated for addresses. Each one is right
         justified in that field and padded on the left with spaces, or zeros, to
         fill the field. Zeros are only used for padding when the first digit of
         the <width> is 0, as it is in the xxd <style>.

         The default <style> is hex and the default <width>, for each <style>, is
         shown in the list.

     --addr-prefix=<string>
         Prepend <string> to the address in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can
         be empty. The default prefix is the empty string.

     --addr-suffix=<string>
         Append <string> to the address in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can
         be empty. The default suffix is a single colon (i.e., ":").

     --background=<color>
     --background=<color>:<selector>
         Sets the background <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's byte or text fields.

         The background <color> should be one of the names in the table

             red            alt-red            bright-red
             green          alt-green          bright-green
             blue           alt-blue           bright-blue
             cyan           alt-cyan           bright-cyan
             magenta        alt-magenta        bright-magenta
             yellow         alt-yellow         bright-yellow
             black          alt-black          bright-black
             white          alt-white          bright-white

         or the word

             reset

         which cancels any background color already assigned to the selected bytes.
         The relative brightness of a <color> tends to increase as you move to the
         right in the table.

         The <selector> is documented below in the SELECTORS section. If <selector>
         and the colon are omitted, <color> is applied to all bytes.

     --byte=<style>
     --byte=<style>:<length>
         The <style> controls how each byte is displayed and it must be one of the
         case-dependent strings in the list:

              binary - bytes are displayed in binary (base 2)
             decimal - bytes are displayed in decimal (base 10)
                 hex - bytes are displayed in lowercase hex (base 16)
                 HEX - bytes are displayed in uppercase hex (base 16)
               octal - bytes are displayed in octal (base 8)
                 xxd - bytes are displayed in lowercase hex (base 16)

               empty - byte fields are all empty. The byte and text fields can't
                       both be empty.

         The optional <length> must be a nonnegative integer that's used to set the
         maximum length of each record in the dump. See the --length option for more
         details.

     --byte-background=<color>
     --byte-background=<color>:<selector>
         Sets the background <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's byte field.

         The available <color> choices are listed under the --background option's
         description. The <selector> is documented below in the SELECTORS section.
         If <selector> and the colon are omitted, <color> is applied to all bytes.

     --byte-foreground=<color>
     --byte-foreground=<color>:<selector>
         Sets the foreground <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's byte field.

         The available <color> choices are listed under the --foreground option's
         description. The <selector> is documented below in the SELECTORS section.
         If <selector> and the colon are omitted, <color> is applied to all bytes.

     --byte-prefix=<string>
         Prepend <string> to the byte field in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can be
         empty. The default prefix is the empty string.

     --byte-separator=<string>
         Use <string> to separate individual bytes in every record that's included
         in the dump. All characters in <string> must be printable or the <string>
         can be empty. The default separator is a single space (i.e., " ").

     --byte-suffix=<string>
         Append <string> to the byte field in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can be
         empty. The default suffix is the empty string.

     --copyright
         Print copyright information on standard output and then exit.

     --foreground=<color>
     --foreground=<color>:<selector>
         Sets the foreground <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's byte or text fields.

         The foreground <color> should be one of the names in the table

             red            alt-red            bright-red
             green          alt-green          bright-green
             blue           alt-blue           bright-blue
             cyan           alt-cyan           bright-cyan
             magenta        alt-magenta        bright-magenta
             yellow         alt-yellow         bright-yellow
             black          alt-black          bright-black
             white          alt-white          bright-white

             blink-red      blink-alt-red      blink-bright-red
             blink-green    blink-alt-green    blink-bright-green
             blink-blue     blink-alt-blue     blink-bright-blue
             blink-cyan     blink-alt-cyan     blink-bright-cyan
             blink-magenta  blink-alt-magenta  blink-bright-magenta
             blink-yellow   blink-alt-yellow   blink-bright-yellow
             blink-black    blink-alt-black    blink-bright-black
             blink-white    blink-alt-white    blink-bright-white

         or the word

             reset

         which cancels any foreground color already assigned to the selected bytes.
         The relative brightness of a <color> tends to increase as you move to the
         right in the table. Foreground colors that start with the "blink-" prefix
         cause all characters displayed in that <color> to blink.

         The <selector> is documented below in the SELECTORS section. If <selector>
         and the colon are omitted, <color> is applied to all bytes.

      -?
     --help
         Print the internal documentation about the program on standard output and
         then exit.

     --length=<length>
         A <length> that's a positive integer is the maximum number of bytes, read
         from the input file, that can be displayed in a single record. Each record
         in a dump, except perhaps the last one, represents exactly <length> input
         file bytes. Each record's byte and text field components are two different
         ways that the dump can use to display those <length> input file bytes. As
         a convenience the --byte and --text options can also set the <length>.

         The default <length> is 16 bytes. If <length> is 0, the entire input file
         is displayed in a single record.

     --license
         Print licensing information on standard output and then exit.

     --narrow
         Each record in the dump starts on a new line, but in this layout style
         only the address and byte fields are printed next to each other on that
         line. The text field prints on the next line, but everything is carefully
         adjusted so each character ends up directly below its corresponding byte.
         The vertical alignment constraints mean that strings set using unrelated
         options (e.g., --byte-separator) may occasionally have to be padded with
         spaces.

         This option is ignored and the default layout style, which is described
         in the --wide option, is used whenever the byte field or the text field
         is empty.

     --read=<count>
         Stop the dump after reading <count> bytes from the input file. <count>
         must be a nonnegative integer and when it's 0 the entire input file is
         read. The default <count> is 0.

     --spacing=<separation>
         The number of newlines used to separate individual records in the dump is
         specified by <separation>, which must be one of the values in the list:

             single - use one newline separate records
                  1 - synonym for single

             double - use two newlines to separate records
                  2 - synonym for double

             triple - use three newlines to separate records
                  3 - synonym for triple

         The default <separation> is single (or 1).

         See the description of the --length option if you want to dump the entire
         input file as a single record. This option only covers the spacing between
         individual records in the dump.

     --start=<address>
     --start=<address>:<output-address>
         Start the dump with the byte at <address> in the input file and use it,
         or the optional <output-address>, as the address that's attached to the
         first record in the output dump. The <address> and <output-address> must
         be nonnegative integers. The default <address> is 0.

     --text=<style>
     --text=<style>:<length>
         The <style> selects the character strings that are used to represent each
         byte in the dump's text field. It must be one of the names in the list:

               ascii - one character strings that only identify bytes that are
                       printable ASCII characters. All other bytes, even the ones
                       that are classified as printable Unicode code points, are
                       represented by a period (i.e., ".").

             unicode - one character strings that identify all bytes that represent
                       printable Unicode code points using the character assigned to
                       to that code point. The rest of the bytes are all represented
                       using a period (i.e., ".").

                       Any byte representing a character that Python determines can't
                       be displayed in the user's locale is replaced by one question
                       mark (i.e., "?").

               caret - two character strings that use a custom extension of caret
                       notation to uniquely represent every byte. Bytes that are
                       printable Unicode code points are represented by character
                       strings that start with a space and end with the printable
                       Unicode character assigned to that byte.

                       The rest of the bytes are assigned to Unicode code points
                       that aren't printable characters. The two character strings
                       used to represent them all start with a caret (i.e., "^")
                       and end with a unique printable character that's selected
                       using the formula

                           (byte + 0x40) % 0x80

                       when the unprintable byte is ASCII (i.e., byte < 0x80) and

                           (byte + 0x40) % 0x80 + 0x80

                       when it's not ASCII (i.e., byte >= 0x80). The extension of
                       caret notation beyond ASCII was done to make sure each byte
                       in an input file could be identified from the two character
                       strings displayed in the text field. It's not a necessary
                       constraint, because the byte field is always available, but
                       it seems like reasonable goal.

                       Any byte representing a character that Python determines can't
                       be displayed in the user's locale is replaced by two question
                       marks (i.e., "??").

              escape - two character strings that use C-style escapes to represent
                       unprintable bytes with numeric values that are the same as
                       two character C-style backslash escape sequences. All other
                       bytes are represented by two character strings described in
                       the caret <style> section.

                       Any byte representing a character that Python determines can't
                       be displayed in the user's locale is replaced by two question
                       marks (i.e., "??").

                 xxd - duplicates the text field display style that the xxd command
                       produces. It's just a synonym for ascii and is only included
                       for consistency with the --addr and --byte options.

               empty - text fields are all empty. The text and byte fields can't
                       both be empty.

         The default <style> is ascii.

         The optional <length> must be a nonnegative integer that's used to set the
         maximum length of each record in the dump. See the --length option for more
         details.

     --text-background=<color>
     --text-background=<color>:<selector>
         Sets the background <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's text field.

         The available <color> choices are listed under the --background option's
         description. The <selector> is documented below in the SELECTORS section.
         If <selector> and the colon are omitted, <color> is applied to all bytes.

     --text-foreground=<color>
     --text-foreground=<color>:<selector>
         Sets the foreground <color> that's used when any of the bytes selected by
         <selector> are displayed in the dump's text field.

         The available <color> choices are listed under the --foreground option's
         description. The <selector> is documented below in the SELECTORS section.
         If <selector> and the colon are omitted, <color> is applied to all bytes.

     --text-prefix=<string>
         Prepend <string> to the text field in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can be
         empty. The default prefix is the empty string.

     --text-suffix=<string>
         Append <string> to the text field in every record that's included in the
         dump. All characters in <string> must be printable or the <string> can be
         empty. The default suffix is the empty string.

     --version
         Print version information on standard output and then exit.

     --wide
         Each record in a dump always starts on a new line and in this layout the
         address, byte, and text field components are arranged in that order and
         printed on the same line. This is the default layout.

         The implementation of this layout is straightforward and doesn't require
         changes to settings specified by unrelated options. The --narrow option
         can be used to request the other supported layout.

 SELECTORS
 =========

 All background and foreground options expect to find a <selector> in their argument
 that picks all the bytes targeted by that option. The <selector> consists of one or
 more space separated tokens that can be integers, integer ranges, character classes,
 or raw strings (that use a slightly modified notation borrowed from Rust).

 A <selector> that starts with an optional base prefix and is followed by tokens that
 are completely enclosed in a single set of parentheses picks the base that's used to
 evaluate every integer and integer range token in <selector>. For example,

     0x(token1 token2 token3 token4 ...)

 is valid syntax that uses "0x" to pick the base used to evaluate every number in the
 tokens that are enclosed in parentheses. A base prefix that's "0x" or "0X" means all
 numbers are hex, "0" means they're all octal, and no base prefix means the numbers
 are all decimal. If a base is set using this syntax, every character that appears in
 every number in the tokens must be a valid digit in that base.

 Any of the following tokens are recognized in a <selector>:

     Integer
         Whenever a <selector> has set a base, using the syntax described above, all
         characters in every integer token in that <selector> must be digits in that
         base. Otherwise C-style syntax is used, so hex integers start with "0x" or
         "0X", octal integers start with "0", and decimal integers always start with
         a nonzero decimal digit. Integers that don't represent a byte are ignored.

     Integer Range
         A pair of integer tokens separated by '-' represents a closed interval that
         extends from the left end point to the right end point. Both end points of
         an integer range must be written in the same base. All rules that apply to
         integer tokens apply to both end points. Any part of an integer range that
         doesn't represent a byte is ignored.

     Character Class
         A character class uses a short, familiar lowercase name to select a group
         of bytes. Those names must be bracketed by "[:" and ":]" in the <selector>
         to be recognized as a character class. The 15 character classes that are
         allowed in a <selector> are:

             [:alnum:]      [:digit:]      [:punct:]
             [:alpha:]      [:graph:]      [:space:]
             [:blank:]      [:lower:]      [:upper:]
             [:cntrl:]      [:print:]      [:xdigit:]

             [:ascii:]      [:latin1:]     [:all:]

         The first four rows are the 12 character classes that are defined in the
         POSIX standard. They should be familiar because they're supported by most
         regular expression implementations. The last row are 3 character classes
         that we support because they seem like a convenient way to select familiar
         (or otherwise obvious) blocks of contiguous bytes.

     Raw String
         A modified version of Rust's raw string literal can be used as a token in a
         <selector>. They start with a prefix that's the letter 'r', zero or more '#'
         characters, and a single or double quote, and they always end with a suffix
         that matches the quote and the number of '#' characters used in the prefix.
         For example,

               r"aeiouAEIOU"
               r'aeiouAEIOU'
              r#'aeiouAEIOU'#
             r##"aeiouAEIOU"##

         are raw string tokens that select all the bytes that represent vowels. Any
         character, except null, can appear in a raw string. The selected bytes are
         the Unicode code points of the characters in the string that are less than
         256.

         Two quoting styles are supported because those quote delimiters have to be
         protected from your shell on the command line. It's an approach that gives
         you some flexibility when you use these tokens.


 A <selector> can contain one or more of these tokens, so that means there are lots
 of equivalent ways to select bytes. For example, the command line options

     --text-foreground="bright-red:    r'aeiou@0123456789'"
     --text-foreground="bright-red:    r'aeiou'         r'@' r'0123456789'"
     --text-foreground="bright-red:    r'aeiou'         r'@' [:digit:]"
     --text-foreground="bright-red:    r'aeiou'         0x40  0x30-0x39"
     --text-foreground="bright-red: 0x(r'aeiou'           40    30-39)"
     --text-foreground="bright-red: 0x(61 65 69 6F 75     40    30-39)"

 all select exactly the same bytes, namely the lowercase vowels, the '@' character,
 and the decimal digits, and arrange for "bright-red" to be their foreground color
 whenever any of them are displayed in the text field.

 DEBUGGING
 =========

 Even though the program's debugging support is officially undocumented, there are
 a few debug options that users might occasionally be interested in. The three that
 stand out can be added individually

     bytedump-python --debug=settings --debug=bytemap --debug=textmap ...

 or in a comma separated list

     bytedump-python --debug=settings,bytemap,textmap ...

 to any of the example command lines in the next section. Debugging output goes to
 standard error, so it can easily be separated from the generated dump. Organization
 of the debugging output is controlled internally by the program and does not depend
 the command line ordering of the debug options.

 EXAMPLES
 ========

 If you run the program without any command line options, as in

     bytedump-python file

 you get a dump of file using the program's default settings. It's not a dump that
 xxd can duplicate, because the addresses won't exactly match and there aren't xxd
 options that change how it displays addresses (always 8 digit, 0 padded, lowercase
 hex numbers). However, options can control the way this program displays addresses,
 so if you run

     bytedump-python --addr=xxd file

 or equivalently

     bytedump-python --addr=hex:08 file

 you get a dump that should exactly match the output that

     xxd -c16 -g1 file

 generates.

 There are options that give you quite a bit of control over the address, byte, and
 text fields in a dump. For example,

     bytedump-python --addr=decimal --byte=HEX --text=caret file

 prints decimal addresses, uppercase hex bytes, and uses caret notation to represent
 bytes that are displayed in the text field. All three fields will be displayed next
 to each other on a line, but add the --narrow option to the command line

     bytedump-python --narrow --addr=decimal --byte=HEX --text=caret file

 and the layout changes. The text field prints on a line by itself and everything is
 adjusted, by stretching and translation, so every byte displayed in the byte field
 and its representation in the text field end up in the same column.

 Any of the fields can be hidden by setting them to empty, so

     bytedump-python --addr=decimal --byte=binary --text=empty file

 prints decimal addresses, binary (base 2) bytes, and hides the text field, while

     bytedump-python --addr=empty --byte=binary --text=empty file

 just prints the binary (base 2) representation of the bytes. Hiding both the byte
 and text fields doesn't make sense and will result in an error.

 SEE ALSO
 ========

 ascii(7), hexdump(1), iso_8859-1(7), python(1), od(1), xxd(1)
"""

###################################
#
# Guard
#
###################################

if __name__ == "__main__":
    ByteDump.main(sys.argv[1:])
