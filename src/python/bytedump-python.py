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

from io import BytesIO, StringIO
from typing import List, Dict, Optional, Any

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

    PROGRAM_VERSION: str = "0.1"
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
    # bytes (i.e., the numbers) to strings that are supposed to appear in the dump will
    # usually be referred to as "mapping arrays" rather than "mapping lists".`
    #

    ASCII_TEXT_MAP: List[str] = [
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

    UNICODE_TEXT_MAP: List[str] = [
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

    CARET_TEXT_MAP: List[str] = [
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

    CARET_ESCAPE_TEXT_MAP: List[str] = [
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

    byte_map: Optional[List[str]] = None
    text_map: Optional[List[str]] = None

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

    ANSI_ESCAPE: Dict[str, str] = {
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
        #    $'\e[39m'
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
        #    $'\e[49m'
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
    # class to be the first one in this file. Initialization of attribute_tables now
    # happens in the setup() method, which is the first method called by main().
    #

    attribute_tables = None

    #
    # Using the argumentsConsumed class variable means command line option can be
    # handled in a way that resembles the bash version of this program. There are
    # lots of alternatives, but this is appropriate for this program.
    #

    argumentsConsumed: int = 0

    ###################################
    #
    # ByteDump Methods
    #
    ###################################

    @classmethod
    def arguments(cls, args: List[str]) -> None:
        input_stream = None
        arg = None

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

            # Python's "-" check and path access checks
            if arg == "-" or cls.path_is_readable(arg):
                if arg == "-" or not cls.path_is_directory(arg):
                    if arg != "-":
                        try:
                            # In Python, we open the file. 'rb' is crucial for ByteDump.
                            input_stream = open(arg, 'rb')
                            cls.dump(input_stream, sys.stdout)
                            input_stream.close()
                        except (FileNotFoundError, PermissionError):
                            cls.user_error("problem opening input file", arg)
                        except Exception as e:
                            cls.java_error(str(e))
                    else:
                        # Standard Input. In Python, sys.stdin.buffer matches Java's System.in (bytes)
                        cls.dump(sys.stdin.buffer, sys.stdout)
                else:
                    cls.user_error("argument", cls.delimit(arg), "is a directory")
            else:
                cls.user_error("argument", cls.delimit(arg), "isn't a readable file")
        else:
            cls.user_error("too many non-option command line arguments:", cls.delimit_args(args))

    @classmethod
    def byte_selector(cls, attribute: str, tokens: str, output: List[Optional[str]]) -> None:
        manager = RegexManager()
        chars: List[Optional[str]]
        prefix: str
        suffix: str
        body: str
        tail: str
        tokens_start: str
        name: str
        code: int
        base: int
        first: int
        last: int
        index: int
        count: int

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
        # in the other bytedump implementations should help if really want to tackle
        # this method. Lots of regular expressions, but chatbots can help with them.
        #
        # NOTE - the RegexManager class defined later in this file now caches keeps a
        # temporary copy of the matched groups whenever the manager.matched() method
        # succeeds. Those groups can be accessed using manager.cached_groups and they
        # stick around until the next call of manager.matched().
        #

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
                cls.internal_error("selector base prefix", cls.delimit(prefix), "has not been implemented")

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
                            cls.user_error("problem extracting a hex integer from", cls.delimit(tokens_start))
                    elif base == 8:
                        if manager.matched(tokens, "^(([0-7]+)([-]([0-7]+))?)([ \\t]+|$)"):
                            first = int(manager.cached_groups[2], base)
                            last = int(manager.cached_groups[4], base) if manager.cached_groups[4] is not None else first
                            tokens = tokens[len(manager.cached_groups[0]):]
                        else:
                            cls.user_error("problem extracting an octal integer from", cls.delimit(tokens_start))
                    elif base == 10:
                        if manager.matched(tokens, "^(([1-9][0-9]*)([-]([1-9][0-9]*))?)([ \\t]+|$)"):
                            first = int(manager.cached_groups[2], base)
                            last = int(manager.cached_groups[4], base) if manager.cached_groups[4] is not None else first
                            tokens = tokens[len(manager.cached_groups[0]):]
                        else:
                            cls.user_error("problem extracting a decimal integer from", cls.delimit(tokens_start))
                    else:
                        cls.internal_error("base", cls.delimit(str(base)), "has not been implemented")
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
                        cls.user_error("problem extracting an integer from", cls.delimit(tokens_start))
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
                            cls.user_error(cls.delimit(name), "is not the name of an implemented character class")
                else:
                    cls.user_error("problem extracting a character class from", cls.delimit(tokens_start))
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
                            # StringTo.joiner simulation
                            joined_chars = " ".join([c for c in chars if c is not None])
                            cls.byte_selector(attribute, f"0x({joined_chars})", output)
                    else:
                        cls.user_error("all tokens must be space separated in byte selector", cls.delimit(tokens_start))
            else:
                cls.user_error("no valid token found at the start of byte selector", cls.delimit(tokens_start))

    @classmethod
    def debug(cls, *args: str) -> None:
        buffer: List[str]
        col: int
        consumed: Dict[str, Any]
        key: str
        matched: List[str]
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
        # Responsible for important initialization, like the buffering of the input and
        # output streams.
        #
        try:
            # Python file objects are already buffered, but we follow the logic structure.
            # Seeking if input_start > 0
            if cls.DUMP_input_start > 0:
                # read() consumes bytes, acting like skip for non-seekable streams
                input_stream.read(cls.DUMP_input_start)

            if cls.DUMP_input_read > 0:
                input_stream = cls.byte_loader(input_stream, cls.DUMP_input_read)

            # In Python, we write strings to a TextIOWrapper or bytes to a Bufferedwriter.
            # The Java code wraps output in BufferedWriter(OutputStreamWriter).
            # We will try to write strings to the output stream provided.
            # If standard out is used, it handles strings.

            writer = output_stream

            if cls.DUMP_record_length > 0:
                if cls.DUMP_field_flags == cls.BYTE_field_flag:
                    cls.dump_byte_field(input_stream, writer)
                elif cls.DUMP_field_flags == cls.TEXT_field_flag:
                    cls.dump_text_field(input_stream, writer)
                else:
                    cls.dump_all(input_stream, writer)
            else:
                cls.dump_all_single_record(input_stream, writer)

            # We don't close sys.stdout usually, but logic says input.close()
            # input_stream.close() # Managed by caller in Python usually

        except IOError as e:
            cls.java_error(str(e))

    @classmethod
    def dump_all(cls, input_stream, output) -> None:
        #
        # OPTIMIZED: Vectorized using list comprehensions and str.join()
        #
        if cls.DUMP_record_length > 0:
            # Localize lookups for speed
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

                # 1. Address
                if addr_enabled:
                    output.write(addr_prefix)
                    output.write(addr_format % address)
                    output.write(addr_suffix)

                # 2. Bytes
                if byte_enabled:
                    output.write(byte_prefix)
                    output.write(byte_separator.join([byte_map[b] for b in buffer]))
                    if count < record_len and byte_pad_width > 0:
                        output.write(" " * ((record_len - count) * byte_pad_width))
                    output.write(byte_suffix)

                # 3. Text
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
        #
        # OPTIMIZED: Single record dump
        #

        output_byte = output
        # If both enabled, we must buffer text to print it AFTER all bytes
        output_text = StringIO() if (cls.byte_map is not None and cls.text_map is not None) else output

        if cls.DUMP_record_length == 0:
            addr_prefix = cls.ADDR_prefix
            addr_format = cls.ADDR_format
            addr_suffix = cls.ADDR_suffix + cls.ADDR_field_separator

            # These variables update as we loop (prefix becomes separator)
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

                # Address prints only once at the very start
                if addr_enabled:
                    output.write(addr_prefix)
                    output.write(addr_format % address)
                    output.write(addr_suffix)
                    addr_enabled = False

                if byte_enabled:
                    output_byte.write(current_byte_prefix)
                    output_byte.write(byte_separator.join([byte_map[b] for b in buffer]))
                    # After first chunk, the prefix for the next chunk is the separator
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
        #
        # OPTIMIZED: Dump only byte field
        #
        if cls.DUMP_record_length > 0:
            if cls.byte_map is not None:
                byte_map = cls.byte_map
                record_len = cls.DUMP_record_length

                # Check if we have complex formatting (prefixes, suffixes, etc.)
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
                    # Super fast path: no separators, just join bytes directly
                    record_separator = cls.DUMP_record_separator
                    while True:
                        buffer = input_stream.read(record_len)
                        if not buffer: break

                        # Join with empty string
                        output.write("".join([byte_map[b] for b in buffer]))
                        output.write(record_separator)

                output.flush()
            else:
                cls.internal_error("byte mapping array has not been initialized")
        else:
            cls.internal_error("single record dump has not been handled properly")

    @classmethod
    def dump_text_field(cls, input_stream, output) -> None:
        #
        # OPTIMIZED: Dump only text field
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
        # Check for resource file relative to script
        help_file = cls.get_named_resource_as_stream(cls.get_this_class_name() + ".help")
        if help_file is not None:
            # Emulate Scanner(input)
            for line in help_file:
                # Python file iteration includes newlines, strip to match println behavior?
                # Java scanner.nextLine() strips newline.
                print(line.rstrip('\n'))
            help_file.close()
        elif cls.PROGRAM_USAGE is not None:
            print(cls.PROGRAM_USAGE)
            print()

    @classmethod
    def initialize(cls) -> None:
        cls.initialize1_fields()
        cls.initialize2_field_widths()
        cls.initialize3_layout()
        cls.initialize4_maps()
        cls.initialize5_attributes()

    @classmethod
    def initialize1_fields(cls) -> None:
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
                cls.internal_error("address output", cls.delimit(cls.ADDR_output), "has not been implemented")

        if cls.ADDR_format_width_limit > 0:
            if cls.ADDR_digits > cls.ADDR_format_width_limit:
                cls.user_error("address width", cls.delimit(cls.ADDR_format_width), "exceeds the internal limit of", cls.delimit(str(cls.ADDR_format_width_limit)))

        cls.ADDR_prefix_size = len(cls.ADDR_prefix)
        cls.ADDR_suffix_size = len(cls.ADDR_suffix)
        cls.ADDR_field_separator_size = len(cls.ADDR_field_separator)
        cls.ADDR_padding = "0" if cls.ADDR_format_width.startswith("0") else " "

        # TEXT field
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
                cls.internal_error("text output", cls.delimit(cls.TEXT_output), "has not been implemented")

        cls.TEXT_prefix_size = len(cls.TEXT_prefix)
        cls.TEXT_suffix_size = len(cls.TEXT_suffix)
        cls.TEXT_separator_size = len(cls.TEXT_separator)

        if len(cls.TEXT_map) > 0:
            if not cls.has_named_field(cls.TEXT_map):
                cls.internal_error(cls.delimit(cls.TEXT_map), "is not recognized as a TEXT field mapping array name")

        # BYTE field
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
                cls.internal_error("byte output", cls.delimit(cls.BYTE_output), "has not been implemented")

        if len(cls.BYTE_map) > 0:
            if not cls.has_named_field(cls.BYTE_map):
                cls.internal_error(cls.delimit(cls.BYTE_map), "is not recognized as a BYTE field mapping array name")

        cls.BYTE_prefix_size = len(cls.BYTE_prefix)
        cls.BYTE_suffix_size = len(cls.BYTE_suffix)
        cls.BYTE_separator_size = len(cls.BYTE_separator)

        if cls.DUMP_record_length_limit > 0:
            if cls.DUMP_record_length > cls.DUMP_record_length_limit:
                cls.user_error("requested record length", cls.delimit(str(cls.DUMP_record_length)), "exceeds the internal buffer limit of", cls.delimit(str(cls.DUMP_record_length_limit)), "bytes")

    @classmethod
    def initialize2_field_widths(cls) -> None:
        if cls.DUMP_record_length > 0:
            if cls.BYTE_output == "EMPTY" or cls.TEXT_output == "EMPTY" or cls.DUMP_layout == "NARROW":
                cls.BYTE_field_width = 0
            else:
                cls.BYTE_field_width = cls.DUMP_record_length * (cls.BYTE_digits_per_octet + cls.BYTE_separator_size) - cls.BYTE_separator_size
        else:
            cls.BYTE_field_width = 0

    @classmethod
    def initialize3_layout(cls) -> None:
        padding = 0

        if cls.DUMP_layout == "NARROW":
            cls.BYTE_field_separator = "\n"

            padding = cls.BYTE_prefix_size - cls.TEXT_prefix_size
            if padding > 0:
                cls.TEXT_indent = cls.TEXT_indent + f"{'':>{padding}}"
            elif padding < 0:
                cls.BYTE_indent = cls.BYTE_indent + f"{'':>{-padding}}"

            padding = cls.BYTE_digits_per_octet - cls.TEXT_chars_per_octet + cls.BYTE_separator_size - cls.TEXT_separator_size
            if padding > 0:
                cls.TEXT_separator = cls.TEXT_separator + f"{'':>{padding}}"
                cls.TEXT_separator_size = len(cls.TEXT_separator)
            elif padding < 0:
                cls.BYTE_separator = cls.BYTE_separator + f"{'':>{-padding}}"
                cls.BYTE_separator_size = len(cls.BYTE_separator)

            padding = cls.BYTE_digits_per_octet - cls.TEXT_chars_per_octet
            if padding > 0:
                cls.TEXT_prefix = cls.TEXT_prefix + f"{'':>{padding}}"
                cls.TEXT_prefix_size = len(cls.TEXT_prefix)
            elif padding < 0:
                cls.internal_error("chars per octet exceeds digits per octet")

            if cls.ADDR_output != "EMPTY":
                padding = cls.ADDR_prefix_size + cls.ADDR_digits + cls.ADDR_suffix_size + cls.ADDR_field_separator_size
                if padding > 0:
                    cls.TEXT_indent = cls.TEXT_indent + f"{'':>{padding}}"

        elif cls.DUMP_layout != "WIDE":
            cls.internal_error("layout", cls.delimit(cls.DUMP_layout), "has not been implemented")

    @classmethod
    def initialize4_maps(cls) -> None:
        manager: RegexManager
        element: str
        codepoint: int
        encoding: str

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
            # us, so the bash approach seems like a better model to follow.
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
                    cls.internal_error("builder for base", cls.delimit(cls.BYTE_output), "map has not been implemented")
        else:
            cls.byte_map = None

        if cls.TEXT_map is not None and len(cls.TEXT_map) > 0:
            cls.text_map = getattr(cls, cls.TEXT_map, None)
            if cls.text_map is not None:
                manager = RegexManager()
                encoding = sys.stdout.encoding or "utf-8"

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
                cls.internal_error(cls.delimit(cls.TEXT_map), "is not a recognized text mapping array name")
        else:
            cls.text_map = None

    @classmethod
    def initialize5_attributes(cls) -> None:
        manager = RegexManager()
        last = cls.last_encoded_byte()

        # Iterate over attribute_tables
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
    def main(cls, args: List[str]) -> None:

        #
        # This method runs the program, basically by just calling the other methods that
        # do the real work.
        #

        try:
            cls.setup()
            cls.options(args)
            cls.initialize()
            cls.debug()
            cls.arguments(args[cls.argumentsConsumed:])
        except Terminator.ExitException as e:
            message = e.get_message()
            if message is not None and len(message) > 0:
                sys.stderr.write(message + "\n")

            # Cause printStackTrace not strictly needed for parity of output

            if e.get_status() != 0:
                sys.exit(e.get_status())

    @classmethod
    def options(cls, args: List[str]) -> None:
        manager = RegexManager()
        done = False
        arg: str
        attribute: str
        length: str
        mode: str
        optarg: str
        selector: str
        style: str
        target: str
        format_width: str
        next_idx: int = 0

        #
        # A long, but straightforward method that uses RegexManager to process command line options.
        # Uses a while loop to allow manual index manipulation (like skipping args).
        #

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
                                cls.internal_error("option", cls.delimit(arg), "has not been completely implemented")

                        cls.ADDR_output = style
                        if format_width is not None:
                            cls.ADDR_format_width = format_width
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--addr-prefix=":
                    if cls.printable_user_string(optarg):
                        cls.ADDR_prefix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

                case "--addr-suffix=":
                    if cls.printable_user_string(optarg):
                        cls.ADDR_suffix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

                case "--background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_BACKGROUND"))
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

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
                                cls.internal_error("option", cls.delimit(arg), "has not been completely implemented")

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
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--byte-background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--byte-foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--byte-prefix=":
                    if cls.printable_user_string(optarg):
                        cls.BYTE_prefix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

                case "--byte-separator=":
                    if cls.printable_user_string(optarg):
                        cls.BYTE_separator = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

                case "--byte-suffix=":
                    if cls.printable_user_string(optarg):
                        cls.BYTE_suffix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

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
                                    cls.user_error("debugging mode", cls.delimit(mode), "in option", cls.delimit(arg), "is not recognized")

                case "--foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("BYTE_FOREGROUND"))
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--help":
                    cls.help()
                    Terminator.terminate()

                case "--length=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_record_length = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--length-limit=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_record_length = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--license":
                    print(cls.PROGRAM_LICENSE)
                    Terminator.terminate()

                case "--narrow":
                    cls.DUMP_layout = "NARROW"

                case "--read=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$"):
                        cls.DUMP_input_read = int(manager.cached_groups[1], 0)
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

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
                                cls.internal_error("option", cls.delimit(arg), "has not been completely implemented")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--start=":
                    if manager.matched(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$"):
                        cls.DUMP_input_start = int(manager.cached_groups[1], 0)
                        if manager.cached_groups[3] is not None:
                            cls.DUMP_output_start = int(manager.cached_groups[3], 0)
                        else:
                            cls.DUMP_output_start = cls.DUMP_input_start
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

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
                                cls.internal_error("option", cls.delimit(arg), "has not been completely implemented")

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
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--text-background=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("BACKGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_BACKGROUND"))
                        else:
                            cls.user_error("background attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--text-foreground=":
                    if manager.matched(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$"):
                        attribute = manager.cached_groups[1]
                        selector = manager.cached_groups[4] if manager.cached_groups[3] is not None else "0x(00-FF)"
                        if ("FOREGROUND." + attribute) in cls.ANSI_ESCAPE:
                            cls.byte_selector(attribute, selector, cls.attribute_tables.get_table("TEXT_FOREGROUND"))
                        else:
                            cls.user_error("foreground attribute", cls.delimit(attribute), "in option", cls.delimit(arg), "is not recognized")
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "is not recognized")

                case "--text-prefix=":
                    if cls.printable_user_string(optarg):
                        cls.TEXT_prefix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

                case "--text-suffix=":
                    if cls.printable_user_string(optarg):
                        cls.TEXT_suffix = optarg
                    else:
                        cls.user_error("argument", cls.delimit(optarg), "in option", cls.delimit(arg), "contains unprintable characters")

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
                        cls.user_error("invalid option", cls.delimit(arg))

            if done:
                break

            next_idx += 1

        cls.argumentsConsumed = next_idx

    @classmethod
    def setup(cls) -> None:
        #
        # This is where initialization that needs to happen before the command line
        # options are processed can be done. In this case the AttributeTables class
        # definition now follows the definition of the ByteDump class, so we have to
        # wait use its constructor.
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
    def java_error(cls, *args: str) -> None:
        Terminator.error_handler(
            "-prefix=" + cls.PROGRAM_NAME,
            "-tag=JavaError",
            "-info=location",
            "+exit",
            "+frame",
            "--",
            " ".join(args)
        )

    @classmethod
    def range_error(cls, *args: str) -> None:
        Terminator.error_handler(
            "-prefix=" + cls.PROGRAM_NAME,
            "-tag=RangeError",
            "-info",
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
    # ByteDump - Helper Methods
    #
    ###################################

    @classmethod
    def byte_loader(cls, input_stream, limit: int):
        # Reads limit bytes and returns a BytesIO
        buffer = input_stream.read(limit)
        return BytesIO(buffer)

    @classmethod
    def delimit(cls, arg: Any) -> str:
        # Trivial quote wrapping
        return f"\"{str(arg)}\""

    @classmethod
    def delimit_args(cls, args: List[str]) -> str:
        return "\"" + " ".join(args) + "\""

    @classmethod
    def has_named_field(cls, name: str) -> bool:
        return hasattr(cls, name)

    @classmethod
    def get_named_resource_as_stream(cls, name: str):
        # Emulate getResourceAsStream by looking in local dir
        if os.path.exists(name):
            return open(name, 'r', encoding='utf-8')
        return None

    @classmethod
    def get_this_class_name(cls) -> str:
        return cls.__name__

    @classmethod
    def last_encoded_byte(cls) -> int:
        # Java logic: US-ASCII ? 127 : 255.
        # Python default is usually UTF-8 (extends ASCII), so 255
        return 255

    @classmethod
    def path_is_directory(cls, path: str) -> bool:
        return os.path.isdir(path)

    @classmethod
    def path_is_readable(cls, path: str) -> bool:
        return os.access(path, os.R_OK)

    @classmethod
    def printable_user_string(cls, arg: str) -> bool:
        #
        # Just used to make sure that all of the characters in the strings that a user can
        # "add" to our dump using command line options (e.g., --addr-suffix) are printable
        # characters. It's important, because we count characters in those strings to make
        # sure everything in the dump lines up vertically. The bash and Java versions were
        # able to do this by combining locales with appropriate regular expressions, but
        # I'm not sure how to make that approach work in Python. Anyway, what's done here
        # seems to be sufficient.
        #
        printable = False
        if arg.isprintable():
            try:
                #
                # I think this part works - the Python UTF-8 Mode documentation seems to
                # imply that issues with locale.getpreferredencoding() are only enabled
                # (at startup) when LC_CTYPE is C or POSIX.
                #
                encoding = locale.getpreferredencoding(False)
                arg.encode(encoding)
                printable = True
            except UnicodeEncodeError:
                pass
        return printable

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

    def get_table(self, key: str) -> List[Optional[str]]:
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

    def matched_group(self, group_index: int, text: str, regex: str) -> Optional[str]:
        #
        # No group caching by this method, at least right now. Not 100% convinced it's
        # the right approach, but it's also not unreasonable because the RegexManager
        # class was only designed to be be used by the ByteDump class.
        #

        groups = self.matched_groups(text, regex)
        return groups[group_index] if groups and group_index < len(groups) else None

    def matched_groups(self, text: str, regex: str) -> Optional[List[str]]:
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
        arguments: List[str]
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
    def terminate(cls, message: Optional[str] = "", cause: Optional[BaseException] = None,
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
    def message_formatter(cls, args: List[str]) -> str:
        caller: Dict[str, str]
        manager: RegexManager
        groups: Optional[List[str]]
        done: bool
        arg: str
        message: Optional[str]
        optarg: str
        opttag: str
        target: str
        info: Optional[str]
        prefix: Optional[str]
        suffix: Optional[str]
        tag: Optional[str]
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
        def __init__(self, message: Optional[str] = None, cause: Optional[BaseException] = None, status: int = 1):
            super().__init__(message)
            self.status = status
            if cause:
                self.__cause__ = cause

        def get_status(self) -> int:
            return self.status

        def get_message(self) -> str:
            return str(self)

#
# This is the guard that makes sure this Python implementation of bytedump only runs
# if this file was directly executed.
#

if __name__ == "__main__":
    ByteDump.main(sys.argv[1:])
