/*
 * Copyright (C) 2025 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)
 * SPDX-License-Identifier: MIT
 */

import java.io.BufferedInputStream;
import java.io.BufferedWriter;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.InputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.nio.charset.Charset;
import java.nio.charset.CharsetEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashMap;
import java.util.Scanner;

/*
 * This is supposed to be a straightforward translation of the bash version of the
 * bytedump script to Java. My goal, when I started working on the conversion, was
 * building a Java class file that resembled the bytedump bash script closely enough
 * that understanding one implementation would be useful if you decided to dig into
 * the other.
 *
 * The organization and style I used in this file doesn't match what I typically use
 * in Java files. Instead, this file was designed to emphasize similarities with the
 * existing bash version of bytedump.
 *
 *   About Comments
 *      I usually only use C-style block comments, like the one you're reading right
 *      now, outside class definitions. It's a habit I got into in the last century
 *      because it meant a single C-style comment could usually "erase" large chunks
 *      of Java code, and that was often convenient during debugging or development.
 *
 *      NOTE - this doesn't mesh well with javadoc, but it's just a convention that
 *      I would not follow if javadoc comments (for developer documentation) really
 *      made sense. Nothing in this class file deserves javadoc comments, but they
 *      could make sense in RegexManager.java, Terminator.java, and StringTo.java.
 *
 *   About No Package Statement
 *      I wanted a flat directory structure and relatively simple makefile, so none
 *      of these Java files include a package statement. That means everything used
 *      to build the Java version of bytedump lives in this directory, so it's the
 *      only place to look if you want to understand how the Java version works.
 *
 *      NOTE - if you reorganize things and add a package statement you'll also have
 *      to modify the makefile. If I have time and nothing else interesting to do, I
 *      may include an example makefile that deals with Java packages.
 *
 *   About Locales
 *      When the JVM starts it initializes the default locale based on what it finds
 *      in its environment - after that calling Java's
 *
 *          Locale.setDefault()
 *
 *      method is the only way I know to change it. It's a brute force approach that
 *      would have far-reaching effects across the entire JVM, and it's a method I've
 *      never used (or seen used) in any Java application. Instead, applications that
 *      need custom localization can create a properly initialized instance of Java's
 *      Locale class and hand it to methods, like
 *
 *          String.format()
 *
 *      that use it instead of the JVM's default locale. It's such a clean approach,
 *      particularly compared to how bash handles localization, that I really don't
 *      think there's much more to say about it. However, even though this is Java,
 *      a few words about localization in bash scripts might help you appreciate the
 *      difference.
 *
 *      In bash scripts, localization depends on the values assigned to global shell
 *      variables like LC_ALL or LC_CTYPE, and the script itself is responsible for
 *      setting them (often just LC_ALL) whenever it needs to use a specific locale.
 *      Those global shell variables are initialized when bash starts, using values
 *      that it finds in its environment. So locale settings, even the ones that are
 *      inherited from the environment, can be modified anywhere in a bash script and
 *      that can affect the script in ways that often aren't obvious.
 *
 *      For example, suppose a bash script uses a character class, like [:print:], in
 *      a regular expression to validate user input. Whether that regular expression
 *      works (or not) depends on what your script considers "printable" and whether
 *      global locale variables, like LC_ALL, that control what [:print:] matches are
 *      exactly aligned with what your script wants (whenever that regular expression
 *      is used). Unfortunately, just examining the code that's "close to" the regular
 *      expression likely won't tell you what's stored in the global locale variables
 *      that decide what [:print:] matches.
 *
 *   About Regular Expressions
 *      Java regular expressions are solid and well behaved, and they're not plagued
 *      by annoying locale issues that can affect bash regular expressions. They also
 *      support the common regular expression syntax that's discussed in the block of
 *      comments that you'll find by searching for "About Regular Expressions" in the
 *      bash bytedump script. One thing to keep in mind is that the bash version came
 *      first and I didn't put much thought into writing regular expressions in other
 *      languages until I started working on the Java version. In fact, everything in
 *      that block of comments was written after I had a working Java implementation,
 *      so it just documents what exists rather than outlining a "master plan".
 *
 *      The goal, that's hopefully explained in that block of comments, was to end up
 *      with lots of bash regular expressions that were trivial to translate directly
 *      into Java regular expressions. Most regular expressions in the bash version
 *      fit into this category, and in each one the differences between corresponding
 *      Java and bash regular expressions can be traced to how they're represented in
 *      each language. In the Java version of bytedump they're string literals, while
 *      in the bash implementation almost all regular expressions are built from the
 *      characters that follow the =~ regex matching operator. If you're comfortable
 *      reading bash and Java code then differences, like escape sequences and quotes,
 *      should be pretty easy to understand.
 *
 *      Despite any complaints, I really do appreciate how convenient bash's regular
 *      expression matching can be. In a single bash if-statement a script can match
 *      a string against a regular expression, find out whether that match succeeded
 *      or failed, choose exactly what's executed based on the result of that match,
 *      and as a bonus, automatically collect all the matched subexpressions. That's
 *      a lot, and even though Java regular expressions can handle each piece, doing
 *      all of them in a single Java if-statement that "resembles" the bash approach
 *      was an enjoyable puzzle that I think turned out reasonably well.
 *
 *      My answer to that puzzle can be found in the RegexManager.java file, and if
 *      you want more details take a look at the big block of comments at the start
 *      of that file. In fact, there are so many places where regular expressions are
 *      used that a careful look at RegexManager.java might be worthwhile if you're
 *      really interested in understanding the Java implementation of bytedump.
 *
 * Just like the bash version, the source code in this class file is organized into
 * sections that are discussed next. All of the top-level headings in the next block
 * of comments are also used in comments that mark where each section starts in the
 * source code. Search for any heading and you'll find it in these comments and the
 * comment that shows you where that section starts in the source code.
 *
 * So here are the sections, listed in the same order that you'll find them in the
 * source code, along with a few sentences about each section:
 *
 *   ByteDump Fields
 *      These are the static fields that belong to this class. Instance fields would
 *      also be found here, but there aren't any constructors, so everything defined
 *      in this class is static.
 *
 *      NOTE - some of the field names in this class don't follow normal Java naming
 *      conventions. The exceptions are very unusual names that are discussed in the
 *      comments right before they're used in declarations. If you're curious don't
 *      worry - you won't be able to miss the strange names.
 *
 *   ByteDump Methods
 *      These are the Java methods that "correspond" to functions that can be found
 *      in the "Script Functions" section of the bash version of bytedump. Those two
 *      sets are similar, but they're not identical because there's a really big gap
 *      separating the capabilities of Java and bash.
 *
 *   Error Methods
 *      The Java code that was designed to handle errors in this application can be
 *      found in Terminator.java, so that's where to look for the low level details.
 *      The methods defined in this section are simple convenience methods that make
 *      sure the Terminator.errorHandler() method is called with the arguments that
 *      arrange to print the appropriate error message right before the application
 *      exits.
 *
 *      The low level details involved in gracefully shutting down a Java application
 *      are a little trickier than you might expect. If you're curious take a look at
 *      the methods defined in this section, the main() method defined in this class,
 *      and the Terminator.errorHandler() method that's defined in Terminator.java.
 *
 *   Helper Methods
 *      Some short methods that are occasionally useful in this class, but don't have
 *      counterparts in the bash version of bytedump. They're all fairly simple, but
 *      about half of them rely on Java reflection, and if that's a topic you're not
 *      familiar with then you'll probably find some of these methods confusing.
 *
 *      My guess is most Java programmers have never used reflection, so don't worry
 *      if you belong to that set - I doubt you really need a solid understanding of
 *      it to read this class. However, if you have a strong Java foundation and just
 *      want to learn more about reflection then
 *
 *          https://docs.oracle.com/javase/tutorial/reflect/index.html
 *
 *      and
 *
 *          https://docs.oracle.com/javase/8/docs/api/
 *
 *      should be good references.
 *
 */

public
class ByteDump {

    ///////////////////////////////////
    //
    // ByteDump Fields
    //
    ///////////////////////////////////

    //
    // Program information.
    //

    private static final String PROGRAM_VERSION = "0.9";
    private static final String PROGRAM_DESCRIPTION = "Java reproduction of the bash bytedump script";
    private static final String PROGRAM_COPYRIGHT = "Copyright (C) 2025 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)";
    private static final String PROGRAM_LICENSE = "SPDX-License-Identifier: MIT";

    //
    // The string assigned to PROGRAM_NAME constant is only used in error and usage
    // messages. It's supposed to be the system property that's associated with the
    // "program.name" key, but if it's not defined we use "bytedump" as the name of
    // this program.
    //
    // NOTE - the java command's -D option exists so system properties can be added
    // from the command line that's used to launch a Java application. Once that's
    // done, the launched Java application can just use various System.getProperty()
    // methods to recover system properties that were added by the java command.
    //
    // If you want to see this in action type
    //
    //     make
    //
    // to build this Java application and then run it by typing
    //
    //     ./bytedump-java --launcher-debug /etc/hosts
    //
    // and you'll see debugging output that precedes the actual dump and includes a
    // java command line that looks something like
    //
    //     CLASSPATH='/some/where/bytedump-java.jar' 'java' -Dprogram.name='bytedump-java' 'ByteDump' '/etc/hosts'
    //
    // Notice the -D option that associates the "program.name" key with the basename
    // of the bash script that built the command line. That's how the program's name
    // ends up in Java's system properties Hashtable.
    //
    // If you want to experiment some more just take Java command line that printed
    // on your terminal (not the command line I included in these comments) and run
    // it. Make an intentional mistake, like dumping a non-existent file or using an
    // unsupported option, and you should see an error message that uses the string
    // that the -D option assigned to the program.name key.
    //

    private static final String PROGRAM_NAME = getSystemProperty("program.name", "bytedump");

    //
    // Right now PROGRAM_USAGE is only used if there's no help file in the jar file
    // that was used to launch this application.
    //

    private static final String PROGRAM_USAGE = "Usage: " + PROGRAM_NAME + " [OPTIONS] [FILE|-]";

    //
    // The next "block" of field definitions correspond to many of the elements that
    // the bash version of bytedump managed in the SCRIPT_STRINGS associative array.
    // Keys in that array were period separated tokens that start with an uppercase
    // word and are always followed by one or more lowercase words. SCRIPT_STRINGS
    // managed data that could be used anywhere in the bytedump bash script without
    // creating lots of new global variables.
    //
    // It was convenient in a bash script where performance was never a realistic
    // goal, but it's definitely not an approach that belongs in a Java application.
    // Instead, this implementation uses properly typed class variables with names
    // that are underscore separated words that start with an uppercase word and are
    // always followed by one or more lowercase words. It's not a naming convention
    // you'll find mentioned in Java style guides, but after some false starts I'm
    // convinced it's appropriate and significantly better than the alternatives.
    //
    // The variable names are hard to miss and easy to connect back to strings you
    // might expect to find in the bash version's SCRIPT_STRINGS associative array.
    // There's not a one-to-one correspondence between the SCRIPT_STRINGS keys and
    // these variables names, but there's enough overlap that I think it's a useful
    // convention.
    //
    // NOTE - debugging code that dumped the contents of STRING_STRINGS in the bash
    // version was important and pretty easy to implement. Something like it in this
    // version was also useful, but reflection was used to identify and inspect the
    // appropriate class variables.
    //

    //
    // This wasn't the approach I started with. Instead, I naively began by trying
    // to replicate the SCRIPT_STRINGS associative array that the bash version used
    // with a class named StringMap that was an extension of Java's HashMap. It had
    // a varargs constructor that made it easy to declare and initialize a StringMap
    // in a way that resembled how SCRIPT_STRINGS was created by the bash version,
    // but that really was the only successful part of the StringMap approach.
    //
    // The real problem was that lots of strings stored in SCRIPT_STRINGS represent
    // numbers. Bash happily converts those strings to integers when they're used
    // in arithmetic expressions, but that "trick" doesn't work in Java. Instead,
    // StringMap needed getters and setters to deal with strings that represented
    // integers, so expressions that used (or modified) them were much uglier than
    // the corresponding bash expressions. However, the worst result was that using
    // a StringMap pushed compile-time errors, that javac could easily detect, to
    // runtime mistakes that had to be executed to be noticed.
    //
    // In hindsight, the StringMap approach was such an obvious mistake that I just
    // can't believe how long I stuck with it. Eventually I decided to use properly
    // typed class variables with names that were obtained by replacing the periods
    // in the bash version's SCRIPT_STRINGS keys with underscores. The result was
    // lots of unusual variable names. It's not a Java style I've seen before and
    // I would guess you've never encountered it either, but I believe (after lots
    // of trial and error) that it's the best approach for this class.
    //

    //
    // Overall dump settings.
    //

    private static int    DUMP_field_flags = 0;
    private static int    DUMP_input_read = 0;
    private static int    DUMP_input_maxbuf = 0xFFFF;
    private static int    DUMP_input_start = 0;
    private static String DUMP_layout = "WIDE";
    private static String DUMP_layout_default = "WIDE";
    private static int    DUMP_output_start = 0;
    private static int    DUMP_record_length = 16;
    private static int    DUMP_record_length_limit = 4096;
    private static String DUMP_record_separator = "\n";
    private static String DUMP_unexpanded_char = "?";

    //
    // Values associated with the ADDR, BYTE, and TEXT fields in our dump. Some of
    // them are changed by command line options, while many others are used or set
    // by the initialization code that runs after all of the options are processed.
    //
    // NOTE - there's only one variable with "xxd" in it's name and it's only used
    // to tell String.format() the default width of the address field in xxd dumps.
    //

    private static String ADDR_output = "HEX-LOWER";
    private static int    ADDR_digits = 0;
    private static int    ADDR_field_flag = 0x01;
    private static String ADDR_field_separator = " ";
    private static int    ADDR_field_separator_size = 1;
    private static String ADDR_format = "";
    private static String ADDR_format_width = "";
    private static String ADDR_format_width_default = "6";
    private static String ADDR_format_width_default_xxd = "08";
    private static int    ADDR_format_width_limit = 0;
    private static String ADDR_padding = " ";
    private static String ADDR_prefix = "";
    private static int    ADDR_prefix_size = 0;
    private static int    ADDR_radix = -1;
    private static String ADDR_suffix = ":";
    private static int    ADDR_suffix_size = 1;

    private static String BYTE_output = "HEX-LOWER";
    private static int    BYTE_digits_per_octet = -1;
    private static int    BYTE_field_flag = 0x02;
    private static String BYTE_field_separator = "  ";
    private static int    BYTE_field_width = 0;
    private static String BYTE_indent = "";
    private static String BYTE_map = "";
    private static String BYTE_prefix = "";
    private static int    BYTE_prefix_size = 0;
    private static String BYTE_separator = " ";
    private static int    BYTE_separator_size = 1;
    private static String BYTE_suffix = "";
    private static int    BYTE_suffix_size = 0;

    private static String TEXT_output = "ASCII";
    private static int    TEXT_chars_per_octet = -1;
    private static int    TEXT_field_flag = 0x04;
    private static String TEXT_indent = "";
    private static String TEXT_map = "";
    private static String TEXT_prefix = "";
    private static int    TEXT_prefix_size = 0;
    private static String TEXT_separator = "";
    private static int    TEXT_separator_size = 0;
    private static String TEXT_suffix = "";
    private static int    TEXT_suffix_size = 0;
    private static String TEXT_unexpanded_string = "";

    //
    // Debugging keys that can be changed by command line options. None of them are
    // officially documented, but they are occasionally referenced in comments that
    // you'll find in the source code.
    //
    // NOTE - dropped debugging keys found in the bash version that aren't needed or
    // just don't make sense in this version. The DEBUG_fields key is responsible for
    // generating the kind of output that "DEBUG.strings" did in the bash version. It
    // relies on reflection to access all the class fields and then uses the prefixes
    // (defined below in DEBUG_fields_prefixes) to pick the interesting fields.
    //

    private static boolean DEBUG_addresses = false;
    private static boolean DEBUG_background = false;
    private static boolean DEBUG_bytemap = false;
    private static String  DEBUG_charclass = null;
    private static int     DEBUG_charclass_flags = RegexManager.FLAGS_DEFAULT;
    private static String  DEBUG_charclass_regex = null;
    private static boolean DEBUG_fields = false;
    private static boolean DEBUG_foreground = false;
    private static boolean DEBUG_textmap = false;
    private static boolean DEBUG_unexpanded = false;

    //
    // The value assigned to DEBUG_fields_prefixes are the space separated prefixes of
    // the field names that are dumped when the --debug=fields option is used. Change
    // the list if you want a different collection fields or have them presented in a
    // different order.
    //
    // NOTE - the bash version could just look for "keys" in an associative array, but
    // in this Java implementation we have to use reflection to find the appropriately
    // named class variables.
    //

    private static String DEBUG_fields_prefixes = "DUMP ADDR BYTE TEXT DEBUG PROGRAM";

    //
    // Dumps that this program produces never depend on an external program to generate
    // any part of final dump. That's different than the bash implementation, which was
    // really forced to rely on an external program, like xxd, to read individual bytes
    // from an input file. This is a much better approach, but means we'll usually need
    // TEXT and BYTE field mapping arrays. The only exceptions happen when those fields
    // are explicitly excluded from the dump by command line options.
    //
    // The first group of mapping arrays are for the TEXT field, and just like the bash
    // version, we want to control the expansion of Unicode escape sequences. That's why
    // two backslashes introduce each Unicode escape sequence that appears in the string
    // literals that initialize TEXT field mapping arrays. They postpone the expansions
    // so they don't happen when javac runs, but that delay means any TEXT field mapping
    // array always must be postprocessed (by initialize4_Maps()) before it can be used
    // to map bytes to the character strings that appear in the dump's TEXT field.
    //
    // If you're a little confused by the last paragraph, take a look at
    //
    //     https://docs.oracle.com/javase/specs/jls/se8/html/jls-3.html#jls-3.3
    //
    // which documents how javac handles Unicode escape sequences, and
    //
    //     https://docs.oracle.com/javase/specs/jls/se8/html/jls-3.html#jls-3.10.5
    //
    // where Java's String literals are described in great detail. Both are links in the
    // official Java Language Specification for version 1.8 and are worth a quick look,
    // even if you're an experienced Java programmer. I found the paragraph in section
    // 3.10.5 that talks about Unicode escapes versus standard character escapes, like
    // "\n" and "\r", very useful, particularly when combined with section 3.3.
    //
    // There are some things you can try with this program if you want to experiment a
    // little with Unicode escapes and TEXT field mapping arrays. Type something like
    //
    //     ./bytedump-java --text=unicode --debug=textmap /dev/null
    //
    // and you'll get a debugging dump of the the final TEXT field mapping array. What
    // you'll see (at least on Linux) depends on your locale, but you're likely using
    // UTF-8 to encode characters, so the textmap debugging dump should be filled with
    // printable Unicode characters and periods (for the bytes that represent control
    // characters).
    //
    // Next, type something like
    //
    //     LC_ALL=C ./bytedump-java --text=unicode --debug=textmap /dev/null
    //
    // or
    //
    //     LC_ALL=C ./bytedump-java --text=caret --debug=textmap /dev/null
    //
    // to force the C locale and ASCII character encoding on bytedump-java. ASCII is a
    // 7-bit encoding, so Unicode escape sequences in the selected TEXT field mapping
    // array that reference code points larger than 0x7F can't be represented in ASCII.
    // Instead, they're replaced by one or two question marks in the final TEXT field
    // mapping array that's built at runtime by initialize4_Maps().
    //

    //
    // The ASCII_TEXT_MAP mapping array is designed to reproduce the ASCII text output
    // that xxd (and other similar programs) generate. Unprintable ASCII characters and
    // all bytes with their top bit set are represented by a period in the TEXT field.
    //

    private static final String[] ASCII_TEXT_MAP = {
        //
        // Basic Latin Block (ASCII)
        //

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

        //
        // Latin-1 Supplement Block
        //

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
    };

    //
    // The UNICODE_TEXT_MAP mapping array is a modified version of the ASCII mapping
    // array that expands the collection of bytes displayed by unique single character
    // strings to the printable characters in Unicode's Latin-1 Supplement Block. All
    // control characters are displayed using the string ".", exactly the way they're
    // handled in the ASCII_TEXT_MAP mapping array.
    //

    private static final String[] UNICODE_TEXT_MAP = {
        //
        // Basic Latin Block (ASCII)
        //

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

        //
        // Latin-1 Supplement Block
        //

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
    };

    //
    // The CARET_TEXT_MAP mapping array maps bytes into printable two character strings
    // that can be used in the TEXT field display. The two character strings assigned to
    // bytes that are Unicode C0 and C1 control codes (and DEL) start with a caret (^)
    // and end with a printable character that's selected using:
    //
    //       Unicode C0 and DEL: (byte + 0x40) % 0x80
    //               Unicode C1: (byte + 0x40) % 0x80 + 0x80
    //
    // The rest of the bytes in the array are printable and the string assigned to each
    // one starts with a space and ends with the Unicode character that represents that
    // byte. The extension of "caret notation" beyond the ASCII block seems reasonable,
    // but as far as I know it's just my own convention.
    //

    private static final String[] CARET_TEXT_MAP = {
        //
        // Basic Latin Block (ASCII)
        //

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

        //
        // Latin-1 Supplement Block
        //

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
    };

    //
    // The CARET_ESCAPE_TEXT_MAP mapping array is a slightly modified version of the
    // CARET_TEXT_MAP array that uses C-style escape sequences, when they're defined,
    // to represent control characters. The remaining control characters are displayed
    // using the caret notation that's already been described.
    //

    private static final String[] CARET_ESCAPE_TEXT_MAP = {
        //
        // Basic Latin Block (ASCII)
        //

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

        //
        // Latin-1 Supplement Block
        //

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
    };

    //
    // Unlike the bash implementation of this program, this version will almost always
    // need a BYTE field mapping array. Rather than building the one mapping array that
    // the program needs after the command line options are processed, which was really
    // easy using bash's brace expansion, we declare them all here and let javac do all
    // the work for us.
    //

    private static final String[] BINARY_BYTE_MAP = {
        "00000000", "00000001", "00000010", "00000011", "00000100", "00000101", "00000110", "00000111",
        "00001000", "00001001", "00001010", "00001011", "00001100", "00001101", "00001110", "00001111",
        "00010000", "00010001", "00010010", "00010011", "00010100", "00010101", "00010110", "00010111",
        "00011000", "00011001", "00011010", "00011011", "00011100", "00011101", "00011110", "00011111",
        "00100000", "00100001", "00100010", "00100011", "00100100", "00100101", "00100110", "00100111",
        "00101000", "00101001", "00101010", "00101011", "00101100", "00101101", "00101110", "00101111",
        "00110000", "00110001", "00110010", "00110011", "00110100", "00110101", "00110110", "00110111",
        "00111000", "00111001", "00111010", "00111011", "00111100", "00111101", "00111110", "00111111",
        "01000000", "01000001", "01000010", "01000011", "01000100", "01000101", "01000110", "01000111",
        "01001000", "01001001", "01001010", "01001011", "01001100", "01001101", "01001110", "01001111",
        "01010000", "01010001", "01010010", "01010011", "01010100", "01010101", "01010110", "01010111",
        "01011000", "01011001", "01011010", "01011011", "01011100", "01011101", "01011110", "01011111",
        "01100000", "01100001", "01100010", "01100011", "01100100", "01100101", "01100110", "01100111",
        "01101000", "01101001", "01101010", "01101011", "01101100", "01101101", "01101110", "01101111",
        "01110000", "01110001", "01110010", "01110011", "01110100", "01110101", "01110110", "01110111",
        "01111000", "01111001", "01111010", "01111011", "01111100", "01111101", "01111110", "01111111",
        "10000000", "10000001", "10000010", "10000011", "10000100", "10000101", "10000110", "10000111",
        "10001000", "10001001", "10001010", "10001011", "10001100", "10001101", "10001110", "10001111",
        "10010000", "10010001", "10010010", "10010011", "10010100", "10010101", "10010110", "10010111",
        "10011000", "10011001", "10011010", "10011011", "10011100", "10011101", "10011110", "10011111",
        "10100000", "10100001", "10100010", "10100011", "10100100", "10100101", "10100110", "10100111",
        "10101000", "10101001", "10101010", "10101011", "10101100", "10101101", "10101110", "10101111",
        "10110000", "10110001", "10110010", "10110011", "10110100", "10110101", "10110110", "10110111",
        "10111000", "10111001", "10111010", "10111011", "10111100", "10111101", "10111110", "10111111",
        "11000000", "11000001", "11000010", "11000011", "11000100", "11000101", "11000110", "11000111",
        "11001000", "11001001", "11001010", "11001011", "11001100", "11001101", "11001110", "11001111",
        "11010000", "11010001", "11010010", "11010011", "11010100", "11010101", "11010110", "11010111",
        "11011000", "11011001", "11011010", "11011011", "11011100", "11011101", "11011110", "11011111",
        "11100000", "11100001", "11100010", "11100011", "11100100", "11100101", "11100110", "11100111",
        "11101000", "11101001", "11101010", "11101011", "11101100", "11101101", "11101110", "11101111",
        "11110000", "11110001", "11110010", "11110011", "11110100", "11110101", "11110110", "11110111",
        "11111000", "11111001", "11111010", "11111011", "11111100", "11111101", "11111110", "11111111",
    };

    private static final String[] OCTAL_BYTE_MAP = {
        "000", "001", "002", "003", "004", "005", "006", "007", "010", "011", "012", "013", "014", "015", "016", "017",
        "020", "021", "022", "023", "024", "025", "026", "027", "030", "031", "032", "033", "034", "035", "036", "037",
        "040", "041", "042", "043", "044", "045", "046", "047", "050", "051", "052", "053", "054", "055", "056", "057",
        "060", "061", "062", "063", "064", "065", "066", "067", "070", "071", "072", "073", "074", "075", "076", "077",
        "100", "101", "102", "103", "104", "105", "106", "107", "110", "111", "112", "113", "114", "115", "116", "117",
        "120", "121", "122", "123", "124", "125", "126", "127", "130", "131", "132", "133", "134", "135", "136", "137",
        "140", "141", "142", "143", "144", "145", "146", "147", "150", "151", "152", "153", "154", "155", "156", "157",
        "160", "161", "162", "163", "164", "165", "166", "167", "170", "171", "172", "173", "174", "175", "176", "177",
        "200", "201", "202", "203", "204", "205", "206", "207", "210", "211", "212", "213", "214", "215", "216", "217",
        "220", "221", "222", "223", "224", "225", "226", "227", "230", "231", "232", "233", "234", "235", "236", "237",
        "240", "241", "242", "243", "244", "245", "246", "247", "250", "251", "252", "253", "254", "255", "256", "257",
        "260", "261", "262", "263", "264", "265", "266", "267", "270", "271", "272", "273", "274", "275", "276", "277",
        "300", "301", "302", "303", "304", "305", "306", "307", "310", "311", "312", "313", "314", "315", "316", "317",
        "320", "321", "322", "323", "324", "325", "326", "327", "330", "331", "332", "333", "334", "335", "336", "337",
        "340", "341", "342", "343", "344", "345", "346", "347", "350", "351", "352", "353", "354", "355", "356", "357",
        "360", "361", "362", "363", "364", "365", "366", "367", "370", "371", "372", "373", "374", "375", "376", "377",
    };

    private static final String[] DECIMAL_BYTE_MAP = {
        "  0", "  1", "  2", "  3", "  4", "  5", "  6", "  7", "  8", "  9", " 10", " 11", " 12", " 13", " 14", " 15",
        " 16", " 17", " 18", " 19", " 20", " 21", " 22", " 23", " 24", " 25", " 26", " 27", " 28", " 29", " 30", " 31",
        " 32", " 33", " 34", " 35", " 36", " 37", " 38", " 39", " 40", " 41", " 42", " 43", " 44", " 45", " 46", " 47",
        " 48", " 49", " 50", " 51", " 52", " 53", " 54", " 55", " 56", " 57", " 58", " 59", " 60", " 61", " 62", " 63",
        " 64", " 65", " 66", " 67", " 68", " 69", " 70", " 71", " 72", " 73", " 74", " 75", " 76", " 77", " 78", " 79",
        " 80", " 81", " 82", " 83", " 84", " 85", " 86", " 87", " 88", " 89", " 90", " 91", " 92", " 93", " 94", " 95",
        " 96", " 97", " 98", " 99", "100", "101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111",
        "112", "113", "114", "115", "116", "117", "118", "119", "120", "121", "122", "123", "124", "125", "126", "127",
        "128", "129", "130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143",
        "144", "145", "146", "147", "148", "149", "150", "151", "152", "153", "154", "155", "156", "157", "158", "159",
        "160", "161", "162", "163", "164", "165", "166", "167", "168", "169", "170", "171", "172", "173", "174", "175",
        "176", "177", "178", "179", "180", "181", "182", "183", "184", "185", "186", "187", "188", "189", "190", "191",
        "192", "193", "194", "195", "196", "197", "198", "199", "200", "201", "202", "203", "204", "205", "206", "207",
        "208", "209", "210", "211", "212", "213", "214", "215", "216", "217", "218", "219", "220", "221", "222", "223",
        "224", "225", "226", "227", "228", "229", "230", "231", "232", "233", "234", "235", "236", "237", "238", "239",
        "240", "241", "242", "243", "244", "245", "246", "247", "248", "249", "250", "251", "252", "253", "254", "255",
    };

    private static final String[] HEX_LOWER_BYTE_MAP = {
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0a", "0b", "0c", "0d", "0e", "0f",
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "1a", "1b", "1c", "1d", "1e", "1f",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "2a", "2b", "2c", "2d", "2e", "2f",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "3a", "3b", "3c", "3d", "3e", "3f",
        "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "4a", "4b", "4c", "4d", "4e", "4f",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "5a", "5b", "5c", "5d", "5e", "5f",
        "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "6a", "6b", "6c", "6d", "6e", "6f",
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "7a", "7b", "7c", "7d", "7e", "7f",
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "8a", "8b", "8c", "8d", "8e", "8f",
        "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "9a", "9b", "9c", "9d", "9e", "9f",
        "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "aa", "ab", "ac", "ad", "ae", "af",
        "b0", "b1", "b2", "b3", "b4", "b5", "b6", "b7", "b8", "b9", "ba", "bb", "bc", "bd", "be", "bf",
        "c0", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8", "c9", "ca", "cb", "cc", "cd", "ce", "cf",
        "d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "da", "db", "dc", "dd", "de", "df",
        "e0", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "ea", "eb", "ec", "ed", "ee", "ef",
        "f0", "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "fa", "fb", "fc", "fd", "fe", "ff",
    };

    private static final String[] HEX_UPPER_BYTE_MAP = {
        "00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "0A", "0B", "0C", "0D", "0E", "0F",
        "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "1A", "1B", "1C", "1D", "1E", "1F",
        "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "2A", "2B", "2C", "2D", "2E", "2F",
        "30", "31", "32", "33", "34", "35", "36", "37", "38", "39", "3A", "3B", "3C", "3D", "3E", "3F",
        "40", "41", "42", "43", "44", "45", "46", "47", "48", "49", "4A", "4B", "4C", "4D", "4E", "4F",
        "50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "5A", "5B", "5C", "5D", "5E", "5F",
        "60", "61", "62", "63", "64", "65", "66", "67", "68", "69", "6A", "6B", "6C", "6D", "6E", "6F",
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79", "7A", "7B", "7C", "7D", "7E", "7F",
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "8A", "8B", "8C", "8D", "8E", "8F",
        "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "9A", "9B", "9C", "9D", "9E", "9F",
        "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "AA", "AB", "AC", "AD", "AE", "AF",
        "B0", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "BA", "BB", "BC", "BD", "BE", "BF",
        "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "CA", "CB", "CC", "CD", "CE", "CF",
        "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "DA", "DB", "DC", "DD", "DE", "DF",
        "E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "EA", "EB", "EC", "ED", "EE", "EF",
        "F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FA", "FB", "FC", "FD", "FE", "FF",
    };

    //
    // These will be end up being references to the BYTE and TEXT field mapping arrays
    // that need to be used to build the dump that the user wants. They're set during
    // the initialization that happens after the command line options are processed,
    // and if either one ends up null, the associated field will be omitted from the
    // dump. Both fields can't be omitted.
    //
    // NOTE - if you search for these variables by typing something like
    //
    //     /byteMap =
    // or
    //
    //     /textMap =
    //
    // in vim, you'll quickly find the initialization code that builds them.
    //

    private static String[] byteMap = null;
    private static String[] textMap = null;

    //
    // The addrMap array, which is set during initialization, provides an alternative
    // to using String.format() to build the addresses that are displayed in the dump.
    // That approach seems to be a little faster, but the speed improvement probably
    // can only be measured when big files are dumped using a relatively small record
    // length.
    //
    // The addrBuffer array is created and filled with the appropriate padding (spaces
    // or zeros) during initialization and used when address fields are built by using
    // addrMap rather than String.format(). Take a look at dumpFormattedAddress() and
    // the end of initialize4_Maps() for more details.
    //
    // NOTE - if you search for these variables by typing something like
    //
    //     /addrMap =
    //
    // or
    //
    //     /addrBuffer =
    //
    // in vim, you'll quickly find the initialization code that builds them.
    //
    // NOTE - the --debug=addresses option forces String.format() to be used by making
    // sure addrMap remains null after all of the initialization is finished, and that
    // "tells" dumpFormattedAddress() to use String.format().
    //

    private static char[] addrMap = null;
    private static char[] addrBuffer = null;

    //
    // Values stored in the ANSI_ESCAPE StringMap are the ANSI escape sequences used
    // to selectively change the foreground and background attributes (think colors)
    // of character strings displayed in the BYTE and TEXT fields. They're used in
    // initialize5_Attributes() to surround individual character strings in the BYTE
    // or TEXT field mapping arrays with the ANSI escape sequences that enable and
    // then disable (i.e., reset) the requested attribute.
    //
    // Values assigned to the keys defined in ANSI_ESCAPE that start with FOREGROUND
    // are ANSI escape sequences that set foreground attributes, while values assigned
    // to the keys that start with BACKGROUND are ANSI escapes that set the background
    // attributes. Take a look at
    //
    //     https://en.wikipedia.org/wiki/ANSI_escape_code
    //
    // if you want more information about ANSI escape codes.
    //
    // NOTE - StringMap is a HashMap extension that requires keys and values that are
    // Strings and has a varargs constructor. That constructor is why initialization
    // of ANSI_ESCAPE and the SCRIPT_ANSI_ESCAPE bash associative array resemble each
    // other. There was much more to the StringMap class when I began converting the
    // bash version to Java, but now this is the only place StringMap is used.
    //

    private static final StringMap ANSI_ESCAPE = new StringMap(
        //
        // Foregound color escape sequences.
        //

        "FOREGROUND.black", "\u001B[30m",
        "FOREGROUND.red", "\u001B[31m",
        "FOREGROUND.green", "\u001B[32m",
        "FOREGROUND.yellow", "\u001B[33m",
        "FOREGROUND.blue", "\u001B[34m",
        "FOREGROUND.magenta", "\u001B[35m",
        "FOREGROUND.cyan", "\u001B[36m",
        "FOREGROUND.white", "\u001B[37m",

        "FOREGROUND.alt-black", "\u001B[90m",
        "FOREGROUND.alt-red", "\u001B[91m",
        "FOREGROUND.alt-green", "\u001B[92m",
        "FOREGROUND.alt-yellow", "\u001B[93m",
        "FOREGROUND.alt-blue", "\u001B[94m",
        "FOREGROUND.alt-magenta", "\u001B[95m",
        "FOREGROUND.alt-cyan", "\u001B[96m",
        "FOREGROUND.alt-white", "\u001B[97m",

        "FOREGROUND.bright-black", "\u001B[1;30m",
        "FOREGROUND.bright-red", "\u001B[1;31m",
        "FOREGROUND.bright-green", "\u001B[1;32m",
        "FOREGROUND.bright-yellow", "\u001B[1;33m",
        "FOREGROUND.bright-blue", "\u001B[1;34m",
        "FOREGROUND.bright-magenta", "\u001B[1;35m",
        "FOREGROUND.bright-cyan", "\u001B[1;36m",
        "FOREGROUND.bright-white", "\u001B[1;37m",

        //
        // Blinking foreground color escape sequences.
        //

        "FOREGROUND.blink-black", "\u001B[5;30m",
        "FOREGROUND.blink-red", "\u001B[5;31m",
        "FOREGROUND.blink-green", "\u001B[5;32m",
        "FOREGROUND.blink-yellow", "\u001B[5;33m",
        "FOREGROUND.blink-blue", "\u001B[5;34m",
        "FOREGROUND.blink-magenta", "\u001B[5;35m",
        "FOREGROUND.blink-cyan", "\u001B[5;36m",
        "FOREGROUND.blink-white", "\u001B[5;37m",

        "FOREGROUND.blink-alt-black", "\u001B[5;90m",
        "FOREGROUND.blink-alt-red", "\u001B[5;91m",
        "FOREGROUND.blink-alt-green", "\u001B[5;92m",
        "FOREGROUND.blink-alt-yellow", "\u001B[5;93m",
        "FOREGROUND.blink-alt-blue", "\u001B[5;94m",
        "FOREGROUND.blink-alt-magenta", "\u001B[5;95m",
        "FOREGROUND.blink-alt-cyan", "\u001B[5;96m",
        "FOREGROUND.blink-alt-white", "\u001B[5;97m",

        "FOREGROUND.blink-bright-black", "\u001B[5;1;30m",
        "FOREGROUND.blink-bright-red", "\u001B[5;1;31m",
        "FOREGROUND.blink-bright-green", "\u001B[5;1;32m",
        "FOREGROUND.blink-bright-yellow", "\u001B[5;1;33m",
        "FOREGROUND.blink-bright-blue", "\u001B[5;1;34m",
        "FOREGROUND.blink-bright-magenta", "\u001B[5;1;35m",
        "FOREGROUND.blink-bright-cyan", "\u001B[5;1;36m",
        "FOREGROUND.blink-bright-white", "\u001B[5;1;37m",

        //
        // The ANSI escape code that restores the default foreground color is
        //
        //    "\u001B[39m"
        //
        // but in our implementation, an empty string accomplishes the same thing and
        // is a much better choice.
        //

        "FOREGROUND.reset", "",

        //
        // Background color escape sequences - background blinking isn't possible.
        //

        "BACKGROUND.black", "\u001B[40m",
        "BACKGROUND.red", "\u001B[41m",
        "BACKGROUND.green", "\u001B[42m",
        "BACKGROUND.yellow", "\u001B[43m",
        "BACKGROUND.blue", "\u001B[44m",
        "BACKGROUND.magenta", "\u001B[45m",
        "BACKGROUND.cyan", "\u001B[46m",
        "BACKGROUND.white", "\u001B[47m",

        "BACKGROUND.alt-black", "\u001B[100m",
        "BACKGROUND.alt-red", "\u001B[101m",
        "BACKGROUND.alt-green", "\u001B[102m",
        "BACKGROUND.alt-yellow", "\u001B[103m",
        "BACKGROUND.alt-blue", "\u001B[104m",
        "BACKGROUND.alt-magenta", "\u001B[105m",
        "BACKGROUND.alt-cyan", "\u001B[106m",
        "BACKGROUND.alt-white", "\u001B[107m",

        "BACKGROUND.bright-black", "\u001B[1;40m",
        "BACKGROUND.bright-red", "\u001B[1;41m",
        "BACKGROUND.bright-green", "\u001B[1;42m",
        "BACKGROUND.bright-yellow", "\u001B[1;43m",
        "BACKGROUND.bright-blue", "\u001B[1;44m",
        "BACKGROUND.bright-magenta", "\u001B[1;45m",
        "BACKGROUND.bright-cyan", "\u001B[1;46m",
        "BACKGROUND.bright-white", "\u001B[1;47m",

        //
        // The ANSI escape code that restores the default background color is
        //
        //    "\u001B[49m"
        //
        // but in our implementation, an empty string accomplishes the same thing and
        // is a much better choice.
        //

        "BACKGROUND.reset", "",

        //
        // Reset all escape sequences. Omitting the 0 should work, but decided against
        // it - at least for now.
        //

        "RESET.attributes", "\u001B[0m"
    );

    //
    // The AttributeTables class was written quickly and only designed for superficial
    // cleanup of the four arrays that the bash version used to manage the "attributes"
    // (think colors) that could be applied to the BYTE and TEXT fields using command
    // line options. I can imagine spending more time on a better design, but I think
    // that's a job that belongs in a different Java implementation of bytedump.
    //

    private static AttributeTables attributeTables = new AttributeTables(
        "BYTE_BACKGROUND", "BYTE_FOREGROUND",
        "TEXT_BACKGROUND", "TEXT_FOREGROUND"
    );

    //
    // Using the argumentsConsumed class variable means command line arguments can be
    // handled in a way that resembles the bash version of this program. Java programs
    // have lots alternatives, but that's something that can be addressed elsewhere.
    //

    private static int argumentsConsumed = 0;

    ///////////////////////////////////
    //
    // ByteDump Methods
    //
    ///////////////////////////////////

    private static void
    arguments(String[] args) {

        InputStream input;
        String      arg;

        //
        // Expects at most one argument, which must be "-" or the name of a readable
        // file that's not a directory. Standard input is read when there aren't any
        // arguments or when "-" is the only argument. A representation of the bytes
        // in the input file are written to standard output in a style controlled by
        // the command line options.
        //
        // Treating "-" as an abbreviation for standard input, before checking to see
        // if it's the name of a readable file or directory in the current directory,
        // matches the way Linux commands typically handle it. A pathname containing
        // at least one "/" (e.g., ./-) is how to reference a file named "-" on the
        // command line.
        //

        if (args.length <= 1) {
            arg = (args.length > 0) ? args[0] : "-";
            if (arg.equals("-") || pathIsReadable(arg)) {
                if (arg.equals("-") || pathIsDirectory(arg) == false) {
                    if (arg.equals("-") == false) {
                        try {
                            input = new FileInputStream(arg);
                            dump(input, System.out);
                            input.close();
                        } catch (FileNotFoundException | SecurityException e) {
                            userError("problem opening input file", arg);
                        } catch (IOException e) {
                            javaError(e.getMessage());
                        }
                    } else {
                        dump(System.in, System.out);
                    }
                } else {
                    userError("argument", delimit(arg), "is a directory");
                }
            } else {
                userError("argument", delimit(arg), "isn't a readable file");
            }
        } else {
            userError("too many non-option command line arguments:", delimit(args));
        }
    }


    private static void
    byteSelector(String attribute, String input, String[] output) {

        RegexManager manager;
        String[]     groups;
        String[]     chars;
        String       prefix;
        String       suffix;
        String       body;
        String       tail;
        String       input_start;
        String       name;
        int          code;
        int          base;
        int          first;
        int          last;
        int          index;
        int          count;

        //
        // Called to parse a string that's supposed to assign an attribute (primarily
        // a color) to a group of bytes whenever any of them is displayed in the BYTE
        // or TEXT fields of the dump that this program produces. There's some simple
        // recursion used to implement "character classes" and "raw strings", but the
        // initial call is always triggered by a command line option.
        //
        // The first argument is a string that identifies the attribute that the user
        // wants applied to the bytes selected by the second argument. This method's
        // job is to figure out the numeric values of the selected bytes and associate
        // the attribute (i.e., the first argument) with each byte's numeric value in
        // the string array that's referenced by the third argument.
        //
        // The second argument is the byte "selector" and it's processed using regular
        // expressions. The selector consists of space separated tokens that represent
        // integers, integer ranges, character classes, and a modified implementation
        // of Rust raw string literals.
        //
        // A selector string that starts with an optional base prefix and is followed
        // by tokens that are completely enclosed in a single set of parentheses picks
        // the base used to evaluate all numbers in the selector. A base prefix that's
        // "0x" or "0X" means all numbers are hex, "0" means they're all octal, and no
        // base prefix (just the parens) means they're all decimal. Setting the default
        // base this way, instead of using an option, makes it easy for the user to do
        // exactly the same thing from the command line.
        //
        // If a base is set, all characters in an integer token must be digits in that
        // base. Otherwise C-style syntax is used, so hex integers start with "0x" or
        // "0X", octal integers start with "0", and decimal integers always start with
        // a nonzero decimal digit. An integer range is a pair of integers separated
        // by '-'. It represents a closed interval that extends from the left integer
        // to the right integer. Both end points of a range must be expressed in the
        // same base. Any integer or any part of an integer range that doesn't fit in
        // a byte is ignored.
        //
        // A character class uses a short, familiar lowercase name to select a group
        // of bytes. Those names must be bracketed by "[:" and ":]" in the selector
        // to be recognized as a character class. The 15 character classes that are
        // allowed in a selector are:
        //
        //     [:alnum:]      [:digit:]      [:punct:]
        //     [:alpha:]      [:graph:]      [:space:]
        //     [:blank:]      [:lower:]      [:upper:]
        //     [:cntrl:]      [:print:]      [:xdigit:]
        //
        //     [:ascii:]      [:latin1:]     [:all:]
        //
        // The first four rows are the 12 character classes that are defined in the
        // POSIX standard. The last row are 3 character classes that I decided to
        // support because they seemed like a convenient way to select familiar (or
        // otherwise obvious) blocks of contiguous bytes. This program only deals with
        // bytes, so it's easy to enumerate their members using integers and integer
        // ranges, and that's exactly how this method uses recursion to implement
        // character classes.
        //
        // A modified version of Rust's raw string literal can also be used as a token
        // in the byte selector. They always start with a prefix that's the letter 'r',
        // zero or more '#' characters, and a single or double quote, and they end with
        // a suffix that matches the quote and the number of '#' characters used in the
        // prefix. For example,
        //
        //       r"hello, world"
        //       r'hello, world'
        //      r#'hello, world'#
        //     r##"hello, world"##
        //
        // are valid selectors that represent exactly the same string. Any character,
        // except null, can appear in a raw string that's used as a selector, and the
        // selected bytes are the Unicode code points of the characters in the string
        // that are less than 256. Two quoting styles are supported because the quote
        // delimiters have to be protected from your shell on the command line.
        //
        // NOTE - this is a difficult method to follow, but similarity to what's done
        // in the other bytedump implementations should help if really want to tackle
        // this method. Lots of regular expressions, but chatbots can help with them.
        //

        manager = new RegexManager();
        base = 0;

        //
        // First check for the optional base prefix.
        //

        if ((groups = manager.matchedGroups(input, "^[ \\t]*(0[xX]?)?[(](.*)[)][ \\t]*$")) != null) {
            prefix = groups[1];
            input = groups[2];

            if (prefix == null) {
                base = 10;
            } else if (prefix.equalsIgnoreCase("0x")) {
                base = 16;
            } else if (prefix.equals("0")) {
                base = 8;
            } else {
                internalError("selector base prefix", delimit(prefix), "has not been implemented");
            }
        }

        while ((input = manager.matchedGroup(1, input, "^[ \\t]*([^ \\t].*)")) != null) {
            input_start = input;
            if (manager.matched(input, "^(0[xX]?)?[0-9a-fA-F]")) {
                first = 0;
                last = -1;
                if (base > 0) {
                    if (base == 16) {
                        if ((groups = manager.matchedGroups(input, "^(([0-9a-fA-F]+)([-]([0-9a-fA-F]+))?)([ \\t]+|$)")) != null) {
                            first = Integer.parseInt(groups[2], base);
                            last = (groups[4] != null ? Integer.parseInt(groups[4], base) : first);
                            input = input.substring(groups[0].length());
                        } else {
                            userError("problem extracting a hex integer from", delimit(input_start));
                        }
                    } else if (base == 8) {
                        if ((groups = manager.matchedGroups(input, "^(([0-7]+)([-]([0-7]+))?)([ \\t]+|$)")) != null) {
                            first = Integer.parseInt(groups[2], base);
                            last = (groups[4] != null ? Integer.parseInt(groups[4], base) : first);
                            input = input.substring(groups[0].length());
                        } else {
                            userError("problem extracting an octal integer from", delimit(input_start));
                        }
                    } else if (base == 10) {
                        if ((groups = manager.matchedGroups(input, "^(([1-9][0-9]*)([-]([1-9][0-9]*))?)([ \\t]+|$)")) != null) {
                            first = Integer.parseInt(groups[2], base);
                            last = (groups[4] != null ? Integer.parseInt(groups[4], base) : first);
                            input = input.substring(groups[0].length());
                        } else {
                            userError("problem extracting a decimal integer from", delimit(input_start));
                        }
                    } else {
                        internalError("base", delimit(base), "has not been implemented");
                    }
                } else {
                    if ((groups = manager.matchedGroups(input, "^(0[xX]([0-9a-fA-F]+)([-]0[xX]([0-9a-fA-F]+))?)([ \\t]+|$)")) != null) {
                        first = Integer.parseInt(groups[2], 16);
                        last = (groups[4] != null ? Integer.parseInt(groups[4], 16) : first);
                        input = input.substring(groups[0].length());
                    } else if ((groups = manager.matchedGroups(input, "^((0[0-7]*)([-](0[0-7]*))?)([ \\t]+|$)")) != null) {
                        first = Integer.parseInt(groups[2], 8);
                        last = (groups[4] != null ? Integer.parseInt(groups[4], 8) : first);
                        input = input.substring(groups[0].length());
                    } else if ((groups = manager.matchedGroups(input, "^(([1-9][0-9]*)([-]([1-9][0-9]*))?)([ \\t]+|$)")) != null) {
                        first = Integer.parseInt(groups[2], 10);
                        last = (groups[4] != null ? Integer.parseInt(groups[4], 10) : first);
                        input = input.substring(groups[0].length());
                    } else {
                        userError("problem extracting an integer from", delimit(input_start));
                    }
                }
                if (first <= last && first < 256) {
                    if (last > 256) {
                        last = 256;
                    }
                    for (index = first; index <= last; index++) {
                        output[index] = attribute;
                    }
                }
            } else if (manager.matched(input, "^\\[:")) {
                if ((groups = manager.matchedGroups(input, "^\\[:([a-zA-Z0-9]+):\\]([ \\t]+|$)")) != null) {
                    name = groups[1];
                    input = input.substring(groups[0].length());

                    switch (name) {
                        //
                        // POSIX character class names - these hex mappings were all generated
                        // by this class file (using the --debug-charclass option).
                        //
                        case "alnum":
                            byteSelector(attribute, "0x(30-39 41-5A 61-7A AA B5 BA C0-D6 D8-F6 F8-FF)", output);
                            break;

                        case "alpha":
                            byteSelector(attribute, "0x(41-5A 61-7A AA B5 BA C0-D6 D8-F6 F8-FF)", output);
                            break;

                        case "blank":
                            byteSelector(attribute, "0x(09 20 A0)", output);
                            break;

                        case "cntrl":
                            byteSelector(attribute, "0x(00-1F 7F-9F)", output);
                            break;

                        case "digit":
                            byteSelector(attribute, "0x(30-39)", output);
                            break;

                        case "graph":
                            byteSelector(attribute, "0x(21-7E A1-FF)", output);
                            break;

                        case "lower":
                            byteSelector(attribute, "0x(61-7A AA B5 BA DF-F6 F8-FF)", output);
                            break;

                        case "print":
                            byteSelector(attribute, "0x(20-7E A0-FF)", output);
                            break;

                        case "punct":
                            byteSelector(attribute, "0x(21-23 25-2A 2C-2F 3A-3B 3F-40 5B-5D 5F 7B 7D A1 A7 AB B6-B7 BB BF)", output);
                            break;

                        case "space":
                            byteSelector(attribute, "0x(09-0D 20 85 A0)", output);
                            break;

                        case "upper":
                            byteSelector(attribute, "0x(41-5A C0-D6 D8-DE)", output);
                            break;

                        case "xdigit":
                            byteSelector(attribute, "0x(30-39 41-46 61-66)", output);
                            break;

                        //
                        // Custom character class names.
                        //

                        case "ascii":
                            byteSelector(attribute, "0x(00-7F)", output);
                            break;

                        case "latin1":
                            byteSelector(attribute, "0x(80-FF)", output);
                            break;

                        case "all":
                            byteSelector(attribute, "0x(00-FF)", output);
                            break;

                        default:
                            userError(delimit(name), "is not the name of an implemented character class");
                            break;
                    }
                } else {
                    userError("problem extracting a character class from", delimit(input_start));
                }
            } else if ((groups = manager.matchedGroups(input, "^(r([#]*)(\"|'))")) != null) {
                prefix = groups[1];
                suffix = groups[3] + groups[2];
                input = input.substring(prefix.length());
                if ((tail = manager.matchedGroup(1, input, suffix + "(.*)")) != null) {
                    if (manager.matched(tail, "^([ \\t]|$)")) {
                        body = input.substring(0, input.length() - (suffix.length() + tail.length()));
                        input = tail;

                        chars = new String[256];
                        count = 0;
                        for (index = 0; index < body.length(); index++) {
                            if ((code = body.charAt(index)) < chars.length) {
                                if (chars[code] == null) {
                                    count++;
                                }
                                chars[code] = String.format("%02X", code);
                            }
                        }
                        if (count > 0) {
                            byteSelector(attribute, "0x(" + StringTo.joiner(" ", chars) + ")", output);
                        }
                    } else {
                        userError("all tokens must be space separated in byte selector", delimit(input_start));
                    }
                }
            } else {
                userError("no valid token found at the start of byte selector", delimit(input_start));
            }
        }
    }


    private static void
    debug(String... args) {

        HashMap<String, Object> consumed;
        ArrayList<String>       matched;
        StringBuilder           buffer;
        RegexManager            manager;
        Field[]                 fields;
        String[]                hits;
        String                  name;
        String                  prefix;
        String                  regex;
        String                  sep;
        String                  tag;
        Object                  value;
        int                     flags;
        int                     index;
        int                     first;
        int                     last;
        int                     col;
        int                     row;

        //
        // Takes zero or more arguments that select debugging keys and handles the ones
        // that are supposed to generate immediate output and aren't explicilty handled
        // anywhere else in this class. No arguments selects the most important keys,
        // which currently happens to cover all the cases in the switch statement.
        //
        // NOTE - debug code in the bash version handled the dump of the background and
        // foreground attributes. I moved that responsibility to the dumpTable() method
        // that's defined in the attributeTables class.
        //

        if (args.length == 0) {
            args = new String[] {"foreground", "background", "bytemap", "textmap", "fields", "charclass"};
        }

        for (String arg : args) {
            switch (arg) {
                case "background":
                    if (DEBUG_background) {
                        attributeTables.dumpTable("BYTE_BACKGROUND", "[Debug] ");
                        attributeTables.dumpTable("TEXT_BACKGROUND", "[Debug] ");
                    }
                    break;

                case "bytemap":
                    if (DEBUG_bytemap) {
                        if (byteMap != null) {
                            System.err.printf("[Debug] byteMap[%d]:\n", byteMap.length);
                            for (row = 0; row < 16; row++) {
                                prefix = "[Debug]    ";
                                for (col = 0; col < 16; col++) {
                                    System.err.printf("%s%s", prefix, byteMap[16*row + col]);
                                    prefix=" ";
                                }
                                System.err.println();
                            }
                            System.err.println();
                        }
                    }
                    break;

                case "charclass":
                    if (DEBUG_charclass != null) {
                        regex = DEBUG_charclass_regex;
                        flags = DEBUG_charclass_flags;
                        manager = new RegexManager();
                        hits = null;
                        for (index = 0; index < 256; index++) {
                            if (manager.matched(new String(Character.toChars(index)), regex, flags)) {
                                if (hits == null) {
                                    hits = new String[256];
                                }
                                hits[index] = String.format("%02X", index);
                            }
                        }
                        System.err.println("[Debug] Character Class: [:" + DEBUG_charclass + ":]");
                        System.err.print("[Debug]");
                        if (hits != null) {
                            sep = "    0x(";
                            for (index = 0; index < 256; index++) {
                                if (hits[index] != null) {
                                    first = index;
                                    for (last = index; index < 256; index++) {
                                        if (hits[index] != null) {
                                            last = index;
                                        } else {
                                            break;
                                        }
                                    }
                                    System.err.print(sep + hits[first]);
                                    if (last > first) {
                                        System.err.print("-" + hits[last]);
                                    }
                                    sep = " ";
                                }
                            }
                            System.err.println(")");
                        } else {
                            System.err.println(" -> NO HITS - this should not happen");
                        }
                        System.err.println();
                    }
                    break;

                case "fields":
                    if (DEBUG_fields) {
                        fields = getDeclaredFields();           // this uses reflection
                        buffer = new StringBuilder();
                        consumed = new HashMap<>();
                        for (String prfx : DEBUG_fields_prefixes.split(" ")) {
                            //
                            // Appending and an underscore to prfx might be appropriate, but this
                            // is debugging code, so it's not a big deal. Perhaps better would be
                            // to include those underscores in DEBUG_fields_prefixes.split.
                            //
                            matched = new ArrayList<>();
                            for (Field field : fields) {
                                name = field.getName();
                                if (consumed.containsKey(name) == false && name.startsWith(prfx)) {
                                    matched.add(name);
                                    consumed.put(name, getNamedStaticObject(name));
                                }
                            }

                            if (matched.size() > 0) {
                                Collections.sort(matched);
                                for (String key : matched) {
                                    tag = "  ";
                                    value = consumed.get(key);
                                    if (value == null) {
                                        buffer.append(String.format("[Debug] %s %s=%s\n", tag, key, value));
                                    } else if (value instanceof String) {
                                        buffer.append(String.format("[Debug] %s %s=%s\n", tag, key, StringTo.literal((String)value, true)));
                                    } else {
                                        buffer.append(String.format("[Debug] %s %s=%s\n", tag, key, value.toString()));
                                    }
                                }
                                buffer.append("[Debug]\n");
                            }
                        }
                        System.err.printf("[Debug] Fields[%d]:\n", consumed.size());
                        System.err.println(buffer.toString());
                    }
                    break;

                case "foreground":
                    if (DEBUG_foreground) {
                        attributeTables.dumpTable("BYTE_FOREGROUND", "[Debug] ");
                        attributeTables.dumpTable("TEXT_FOREGROUND", "[Debug] ");
                    }
                    break;

                case "textmap":
                    if (DEBUG_textmap) {
                        if (textMap != null) {
                            System.err.printf("[Debug] textMap[%d]:\n", textMap.length);
                            for (row = 0; row < 16; row++) {
                                prefix = "[Debug]    ";
                                for (col = 0; col < 16; col++) {
                                    System.err.printf("%s%s", prefix, textMap[16*row + col]);
                                    prefix=" ";
                                }
                                System.err.println();
                            }
                            System.err.println();
                        }
                    }
                    break;
            }
        }
    }


    private static void
    dump(InputStream input, OutputStream output) {

        BufferedWriter writer;
        String         mask;

        //
        // Responsible for important initialization, like the buffering of the input and
        // output streams, seeking to the right spot in the InputStream, loading the right
        // number of bytes whenever the user wants to read a fixed number from that stream,
        // and then selecting the final method that's used to generate the dump.
        //
        // NOTE - unlike the original bash version that usually postprocessed xxd output,
        // this program handles all the low level details and does care quite a bit about
        // performance. As a result there are methods that handle unusual dumps, like the
        // ones that want everything displayed as a single record or just want to see the
        // BYTE or TEXT fields. None of those methods make much of a difference, but some
        // careful code duplication, that's compiled by javac, seemed worthwhile. If you
        // disagree it should be trivial to have dumpAll() handle almost everything.
        //

        try {
            input = new BufferedInputStream(input);
            if (DUMP_input_start > 0) {
                input.skip(DUMP_input_start);
            }
            if (DUMP_input_read > 0) {
                input = byteLoader(input, DUMP_input_read);
            }

            writer = new BufferedWriter(new OutputStreamWriter(output));
            if (DUMP_record_length > 0) {
                if (DUMP_field_flags == BYTE_field_flag) {
                    dumpByteField(input, writer);
                } else if (DUMP_field_flags == TEXT_field_flag) {
                    dumpTextField(input, writer);
                } else {
                    dumpAll(input, writer);
                }
            } else {
                dumpAllSingleRecord(input, writer);
            }
            input.close();
        } catch (IOException e) {
            javaError(e.getMessage());
        }
    }


    private static void
    dumpAll(InputStream input, Writer output)

        throws IOException

    {

        String[] byte_map;
        String[] text_map;
        boolean  addr_enabled;
        boolean  byte_enabled;
        boolean  text_enabled;
        String   addr_prefix;
        String   addr_suffix;
        String   byte_prefix;
        String   byte_separator;
        String   byte_suffix;
        String   text_prefix;
        String   text_separator;
        String   text_suffix;
        String   record_separator;
        byte[]   buffer;
        long     address;
        int      count;
        int      index;

        //
        // This is the primary dump method. Even though it can handle everything except
        // single record dumps, I decided to use separate methods (i.e., dumpByteField()
        // and dumpTextField()) to the generate dumps that only include the BYTE or TEXT
        // fields. Each of those methods try to eliminate a little of the overhead that
        // this method needs, and there's a chance that could occasionally be useful.
        //
        // NOTE - local variables are used to save frequently accessed values. They're an
        // attempt to squeeze out a little performance, because accessing local variables
        // should be a little faster than class fields. It's a small optimization that I
        // only reliably measured when I dumped big files.
        //
        // NOTE - the selection of the method that's used to generate the actual dump is
        // made by dump(), so that's where to go if you want to modify my choices.
        //

        if (DUMP_record_length > 0) {
            //
            // Compute strings used in the loop and make sure only local variables are used
            // in that loop. Accessing local variables should be slightly faster than class
            // fields.
            //
            // NOTE - actually, several class fields are referenced in the while loop, but
            // all of them should only be used once - on the last iteration of the loop and
            // only when the number of bytes read didn't completely fill the last record.
            //
            addr_prefix = ADDR_prefix;
            addr_suffix = ADDR_suffix + ADDR_field_separator;
            byte_prefix = BYTE_indent + BYTE_prefix;
            byte_separator = BYTE_separator;
            byte_suffix = BYTE_suffix + BYTE_field_separator;
            text_prefix = TEXT_indent + TEXT_prefix;
            text_separator = TEXT_separator;
            text_suffix = TEXT_suffix;
            record_separator = DUMP_record_separator;

            addr_enabled = (ADDR_format != null && ADDR_format.length() > 0);
            byte_enabled = (byteMap != null);
            text_enabled = (textMap != null);

            byte_map = byteMap;
            text_map = textMap;

            buffer = new byte[DUMP_record_length];
            address = DUMP_output_start;

            while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                if (addr_enabled) {
                    output.write(addr_prefix);
                    dumpFormattedAddress(address, output);
                    output.write(addr_suffix);
                }

                if (byte_enabled) {
                    output.write(byte_prefix);
                    output.write(byte_map[(int)buffer[0]&0xFF]);
                    for (index = 1; index < count; index++) {
                        output.write(byte_separator);
                        output.write(byte_map[(int)buffer[index]&0xFF]);
                    }
                    if (count < buffer.length && BYTE_field_width > 0) {
                        //
                        // Need space padding to properly align the last TEXT field record
                        // with any others that we've printed. Each missing byte needs
                        //
                        //     BYTE_separator_size + BYTE_digits_per_octet
                        //
                        // spaces to guarantee its TEXT field starts in the correct column.
                        //
                        output.write(String.format(
                            "%"
                            + ((buffer.length - count)*(BYTE_digits_per_octet + BYTE_separator_size)) + "s", ""
                        ));
                    }
                    output.write(byte_suffix);
                }

                if (text_enabled) {
                    output.write(text_prefix);
                    output.write(text_map[(int)buffer[0]&0xFF]);
                    for (index = 1; index < count; index++) {
                        output.write(text_separator);
                        output.write(text_map[(int)buffer[index]&0xFF]);
                    }
                    output.write(text_suffix);
                }

                output.write(record_separator);
                address += count;
            }
            output.flush();
        } else {
            internalError("single record dump has not been handled properly");
        }
    }


    private static void
    dumpAllSingleRecord(InputStream input, Writer output)

        throws IOException

    {

        String[] byte_map;
        String[] text_map;
        boolean  addr_enabled;
        boolean  byte_enabled;
        boolean  text_enabled;
        boolean  looped;
        String   addr_prefix;
        String   addr_suffix;
        String   byte_prefix;
        String   byte_separator;
        String   byte_suffix;
        String   text_prefix;
        String   text_separator;
        String   text_suffix;
        Writer   output_byte;
        Writer   output_text;
        byte[]   buffer;
        long     address;
        int      count;
        int      index;

        //
        // Dumps the entire input file as a single record. The TEXT field must be buffered
        // (or saved in a temp file) when it and the BYTE field are supposed to be included
        // in the dump, otherwise TEXT field buffering can be skipped. This dump style won't
        // be used often, so moving it all out of the dumpAll() method made sense. A little
        // code duplication that results in small performance improvements seems worthwhile,
        // particularly because this Java version is pretty fast and really can be used to
        // dump the contents of any file.
        //
        // NOTE - in the bash implementation of this program there's a single function that
        // handles all of the dumps that xxd can't produce. It works by postprocessing xxd
        // output, but doing it all using bash is a painfully slow operation and accepting
        // a little code duplication, the way it's done here, would not make any measurable
        // difference in the performance of that bash function.
        //

        output_byte = output;
        output_text = (byteMap != null && textMap != null) ? new StringWriter() : output;

        if (DUMP_record_length == 0) {
            addr_prefix = ADDR_prefix;
            addr_suffix = ADDR_suffix + ADDR_field_separator;
            byte_prefix = BYTE_indent + BYTE_prefix;
            byte_separator = BYTE_separator;
            byte_suffix = BYTE_suffix + BYTE_field_separator;
            text_prefix = TEXT_indent + TEXT_prefix;
            text_separator = TEXT_separator;
            text_suffix = TEXT_suffix;

            addr_enabled = (ADDR_format != null && ADDR_format.length() > 0);
            byte_enabled = (byteMap != null);
            text_enabled = (textMap != null);

            byte_map = byteMap;
            text_map = textMap;

            buffer = new byte[4096];
            address = DUMP_output_start;
            looped = false;

            while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                if (addr_enabled) {
                    output.write(addr_prefix);
                    dumpFormattedAddress(address, output);
                    output.write(addr_suffix);
                    addr_enabled = false;       // one record ==> one address
                }

                if (byte_enabled) {
                    output_byte.write(byte_prefix);
                    output_byte.write(byte_map[(int)buffer[0]&0xFF]);
                    for (index = 1; index < count; index++) {
                        output_byte.write(byte_separator);
                        output_byte.write(byte_map[(int)buffer[index]&0xFF]);
                    }
                    byte_prefix = byte_separator;
                }

                if (text_enabled) {
                    output_text.write(text_prefix);
                    output_text.write(text_map[(int)buffer[0]&0xFF]);
                    for (index = 1; index < count; index++) {
                        output_text.write(text_separator);
                        output_text.write(text_map[(int)buffer[index]&0xFF]);
                    }
                    text_prefix = text_separator;
                }
                looped = true;
            }

            if (looped) {
                if (byte_enabled) {
                    output.write(byte_suffix);
                    if (text_enabled) {
                        output.write(output_text.toString());
                        output.write(text_suffix);
                    }
                } else {
                    //
                    // The TEXT field has already been written to the output stream.
                    //
                    output.write(text_suffix);
                }
                output.write(DUMP_record_separator);
                output.flush();
            }
        } else {
            internalError("this method can only be called to dump bytes as a single record");
        }
    }


    private static void
    dumpByteField(InputStream input, Writer output)

        throws IOException

    {

        String[] byte_map;
        String   byte_prefix;
        String   byte_separator;
        String   byte_suffix;
        String   record_separator;
        byte[]   buffer;
        int      count;
        int      index;

        //
        // Called to produce the dump when the BYTE field is the only field that's supposed
        // to appear in the output. It won't be used often and isn't even required, because
        // dumpAll() can handle it. However, treating this as an obscure special case means
        // we can eliminate some overhead and that should make this run a little faster.
        //

        if (DUMP_record_length > 0) {
            if (byteMap != null) {
                byte_map = byteMap;
                buffer = new byte[DUMP_record_length];
                if (BYTE_separator.length() > 0 || BYTE_prefix.length() > 0 || BYTE_indent.length() > 0 || BYTE_suffix.length() > 0) {
                    byte_prefix = BYTE_indent + BYTE_prefix;
                    byte_separator = BYTE_separator;
                    byte_suffix = BYTE_suffix + DUMP_record_separator;
                    while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                        output.write(byte_prefix);
                        output.write(byte_map[(int)buffer[0]&0xFF]);
                        for (index = 1; index < count; index++) {
                            output.write(byte_separator);
                            output.write(byte_map[(int)buffer[index]&0xFF]);
                        }
                        output.write(byte_suffix);
                    }
                } else {
                    record_separator = DUMP_record_separator;
                    while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                        for (index = 0; index < count; index++) {
                            output.write(byte_map[(int)buffer[index]&0xFF]);
                        }
                        output.write(record_separator);
                    }
                }
                output.flush();
            } else {
                internalError("byte mapping array has not been initialized");
            }
        } else {
            internalError("single record dump has not been handled properly");
        }
    }


    private static void
    dumpFormattedAddress(long address, Writer output)

        throws IOException

    {

        int index;
        int length;
        int offset;

        //
        // This method is just an attempt to gain a little speed over an implementation
        // that relies entirely on Java's String.format() method. The improvement really
        // isn't much, but it definitely can be measured when you dump big files, using
        // small record sizes, and you send the output to /dev/null. For example, pick
        // any large file on your system (I used /bin/pandoc - it's really big) and run
        // the command
        //
        //     time bytedump-java --length=16 /bin/pandoc >/dev/null
        //
        // several times to see how this method's custom implementation performs. After
        // that add --debug=addresses to the command line
        //
        //     time bytedump-java --debug=addresses --length=16 /bin/pandoc >/dev/null
        //
        // to make sure String.format() is used to generate the dump's addresses. Run it
        // a few times and I'm sure you'll be convinced that String.format() is slower.
        // If you want an extreme example set the record length to 1 (using --length=1),
        // and then every byte will need its own address.
        //
        // NOTE - addrBuffer was initialized with padding characters (currently just zero
        // or space) that are overwritten as the address increases. It's an approach that
        // means this method doesn't have to worry about adding padding characters to the
        // strings that it builds to represent an address. Instead, it builds an address
        // one digit at a time starting with the least significant digit, which overwrites
        // the last character in addrBuffer. Subsequent digits are placed to the left of
        // the preceeding digit in addrBuffer and the process continues until there aren't
        // any address digits left. After that, all this method has to do is decide where
        // the padded address begins in addrBuffer and make sure all those characters are
        // written to the output stream.
        //
        // NOTE - this method intentionally doesn't use local variable references to the
        // addrMap or addrBuffer class variables. Unlike in most of the other low level
        // dump methods, I found it impossible to notice any performance improvement when
        // that approach was used in this method. It's a result that makes sense because
        // loops in this method are pretty short and only one formatted address is needed
        // for each dump record, which by default displays 16 bytes.
        //

        if (addrMap != null) {
            length = addrBuffer.length;
            offset = length - ADDR_digits;
            if (address > 0) {
                index = length;
                switch (ADDR_radix) {
                    case 8:
                        while (address > 0) {
                            addrBuffer[--index] = addrMap[(int)(address % 8)];
                            address /= 8;
                        }
                        break;

                    case 10:
                        while (address > 0) {
                            addrBuffer[--index] = addrMap[(int)(address % 10)];
                            address /= 10;
                        }
                        break;

                    case 16:
                        while (address > 0) {
                            addrBuffer[--index] = addrMap[(int)(address % 16)];
                            address /= 16;
                        }
                        break;

                    default:
                        //
                        // Might be able to handle this using String.format(), but it looks
                        // like an omission that probably should be tracked down.
                        //
                        internalError("radix", delimit(ADDR_radix), "has not been implemented");
                        break;
                }
                //
                // Figure out where the padded address really starts and send all of it to
                // the output stream.
                //
                if (offset < index) {
                    output.write(addrBuffer, offset, ADDR_digits);
                } else {
                    output.write(addrBuffer, index, length - index);
                }
            } else if (address == 0) {
                addrBuffer[length - 1] = '0';
                output.write(addrBuffer, offset, ADDR_digits);
            } else {
                //
                // A precaution, but address is a long and its nonzero starting value that
                // can be set by a command line option has been restricted, so this should
                // never happen.
                //
                output.write(String.format(ADDR_format, address));
            }
        } else {
            output.write(String.format(ADDR_format, address));
        }
    }


    private static void
    dumpTextField(InputStream input, Writer output)

        throws IOException

    {

        String[] text_map;
        String   text_prefix;
        String   text_separator;
        String   text_suffix;
        String   record_separator;
        byte[]   buffer;
        int      count;
        int      index;

        //
        // Called to produce the dump when the TEXT field is the only field that's supposed
        // to appear in the output. It won't be used often and isn't even required, because
        // dumpAll() can handle it. However, treating this as an obscure special case means
        // we can eliminate some overhead and that should make this run a little faster.
        //

        if (DUMP_record_length > 0) {
            if (textMap != null) {
                text_map = textMap;
                buffer = new byte[DUMP_record_length];
                if (TEXT_separator.length() > 0 || TEXT_prefix.length() > 0 || TEXT_indent.length() > 0 || TEXT_suffix.length() > 0) {
                    text_prefix = TEXT_indent + TEXT_prefix;
                    text_separator = TEXT_separator;
                    text_suffix = TEXT_suffix + DUMP_record_separator;
                    while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                        output.write(text_prefix);
                        output.write(text_map[(int)buffer[0]&0xFF]);
                        for (index = 1; index < count; index++) {
                            output.write(text_separator);
                            output.write(text_map[(int)buffer[index]&0xFF]);
                        }
                        output.write(text_suffix);
                    }
                } else {
                    record_separator = DUMP_record_separator;
                    while ((count = input.read(buffer, 0, buffer.length)) > 0) {
                        for (index = 0; index < count; index++) {
                            output.write(text_map[(int)buffer[index]&0xFF]);
                        }
                        output.write(record_separator);
                    }
                }
                output.flush();
            } else {
                internalError("text mapping array has not been initialized");
            }
        } else {
            internalError("single record dump has not been handled properly");
        }
    }


    private static void
    help() {

        InputStream input;
        Scanner     scanner;

        //
        // Nothing fancy to do here - what's displayed (on standard output) is the contents
        // of a text file that should be included in the jar file that's being executed. The
        // name of that file is the name of this class with ".help" appended as the suffix.
        // If we don't find it in the jar file we output PROGRAM_USAGE instead.
        //
        // NOTE - techniques available in a bash script, like a here document or extracting
        // help text from comments in a source file, aren't available in a Java program. We
        // assume Java 1.8, so multiline String literals don't exist, but even if we did try
        // to use a bunch of String literals, we still would have to protect characters in
        // the documentation that need to be escaped (using backslashes) in String literals.
        // Storing the help documentation in a text file that's included in the progam's jar
        // file eliminates that chore.
        //

        if ((input = getNamedResourceAsStream(getThisClassName() + ".help")) != null) {
            scanner = new Scanner(input);
            while (scanner.hasNextLine()) {
                System.out.println(scanner.nextLine());
            }
            scanner.close();
        } else if (PROGRAM_USAGE != null) {
            System.out.println(PROGRAM_USAGE);
            System.out.println();
        }
    }


    private static void
    initialize() {

        //
        // Handles the initialization that happens after all the command line options
        // are processed. The goal is to try to honor all the user's requests and to
        // finish as many calculations as possible before starting the dump. Some of
        // those calculations are difficult, but I think what's done in this version
        // of bytedump is much easier to follow than the original bash implementation.
        //
        // All of the initialization could have been done right here in this method,
        // but there's so much code that splitting the work up into separate methods
        // seemed like a way to make it a little easier to follow. The names of those
        // methods were chosen so their (case independent) sorted order matched the
        // order that they're called. However, no matter how the initialization code
        // is organized, it's still difficult to follow.
        //
        // NOTE - the good news is, if you're willing to believe this stuff works, you
        // probably can skip all the initialization, return to main(), and still follow
        // the rest of the program.
        //
        // NOTE - this program generates every dump, so there's no need to keep track
        // of internal properties of xxd (or any other program) or do any xxd focused
        // initialization. That means the two bash initialization functions that dealt
        // directly with xxd didn't have to be ported to this version.
        //

        initialize1_Fields();
        initialize2_FieldWidths();
        initialize3_Layout();
        initialize4_Maps();
        initialize5_Attributes();
    }


    private static void
    initialize1_Fields() {

        //
        // The main job in this method is to check the output styles for the ADDR, BYTE,
        // and TEXT fields that are set after the command line options are processed and
        // use them to initialize all other fields that depend on the selected style.
        //
        // Bits set in DUMP_field_flags represent the fields that will be printed in the
        // dump. All three fields are enabled when we start. Fields that are "EMPTY" will
        // have their flag bits cleared and when this method returns the flag bits set in
        // DUMP_field_flags represent the fields that are included in the dump.
        //

        DUMP_field_flags = ADDR_field_flag | BYTE_field_flag | TEXT_field_flag;

        switch (ADDR_output) {
            case "DECIMAL":
                ADDR_format_width = (ADDR_format_width.length() > 0) ? ADDR_format_width : ADDR_format_width_default;
                ADDR_format = "%" + ADDR_format_width + "d";
                ADDR_digits = Integer.parseInt(ADDR_format_width, 10);
                ADDR_radix = 10;
                break;

            case "EMPTY":
                ADDR_format_width = "0";
                ADDR_format = "";
                ADDR_digits = 0;
                ADDR_radix = 0;
                DUMP_field_flags &= ~ADDR_field_flag;
                break;

            case "HEX-LOWER":
                ADDR_format_width = (ADDR_format_width.length() > 0) ? ADDR_format_width : ADDR_format_width_default;
                ADDR_format = "%" + ADDR_format_width + "x";
                ADDR_digits = Integer.parseInt(ADDR_format_width, 10);
                ADDR_radix = 16;
                break;

            case "HEX-UPPER":
                ADDR_format_width = (ADDR_format_width.length() > 0) ? ADDR_format_width : ADDR_format_width_default;
                ADDR_format = "%" + ADDR_format_width + "X";
                ADDR_digits = Integer.parseInt(ADDR_format_width, 10);
                ADDR_radix = 16;
                break;

            case "OCTAL":
                ADDR_format_width = (ADDR_format_width.length() > 0) ? ADDR_format_width : ADDR_format_width_default;
                ADDR_format = "%" + ADDR_format_width + "o";
                ADDR_digits = Integer.parseInt(ADDR_format_width, 10);
                ADDR_radix = 8;
                break;

            case "XXD":
                ADDR_output = "HEX-LOWER";
                ADDR_format_width = (ADDR_format_width.length() > 0) ? ADDR_format_width : ADDR_format_width_default_xxd;
                ADDR_format = "%" + ADDR_format_width + "x";
                ADDR_digits = Integer.parseInt(ADDR_format_width, 10);
                ADDR_radix = 16;
                break;

            default:
                internalError("address output", delimit(ADDR_output), "has not been implemented");
                break;
        }

        if (ADDR_format_width_limit > 0) {
            if (ADDR_digits > ADDR_format_width_limit) {
                userError("address width", delimit(ADDR_format_width), "exceeds the internal limit of", delimit(ADDR_format_width_limit));
            }
        }

        //
        // Unlike the bash version, counting the extra characters that print in the ADDR
        // field of the dump is trivial and locale independent, but only because we made
        // sure (in the option handling code) that all those characters are printable.
        //

        ADDR_prefix_size = ADDR_prefix.length();
        ADDR_suffix_size = ADDR_suffix.length();
        ADDR_field_separator_size = ADDR_field_separator.length();

        ADDR_padding = ADDR_format_width.startsWith("0") ? "0" : " ";

        //
        // TEXT field initializations.
        //

        switch (TEXT_output) {
            case "ASCII":
                TEXT_map = "ASCII_TEXT_MAP";
                TEXT_chars_per_octet = 1;
                TEXT_unexpanded_string = "?";
                break;

            case "CARET":
                TEXT_map = "CARET_TEXT_MAP";
                TEXT_chars_per_octet = 2;
                TEXT_unexpanded_string = "??";
                break;

            case "CARET_ESCAPE":
                TEXT_map = "CARET_ESCAPE_TEXT_MAP";
                TEXT_chars_per_octet = 2;
                TEXT_unexpanded_string = "??";
                break;

            case "EMPTY":
                TEXT_map = "";
                TEXT_chars_per_octet = 0;
                TEXT_unexpanded_string = "";
                BYTE_field_separator = "";
                DUMP_layout = DUMP_layout_default;
                DUMP_field_flags &= ~TEXT_field_flag;
                break;

            case "UNICODE":
                TEXT_map = "UNICODE_TEXT_MAP";
                TEXT_chars_per_octet = 1;
                TEXT_unexpanded_string = "?";
                break;

            case "XXD":
                TEXT_output = "ASCII";
                TEXT_map = "ASCII_TEXT_MAP";
                TEXT_chars_per_octet = 1;
                TEXT_unexpanded_string = "?";
                break;

            default:
                internalError("text output", delimit(TEXT_output), "has not been implemented");
                break;
        }

        //
        // Unlike the bash version, counting the extra characters that print in the TEXT
        // field of the dump is trivial and locale independent, but only because we made
        // sure (in the option handling code) that all those characters are printable.
        //

        TEXT_prefix_size = TEXT_prefix.length();
        TEXT_suffix_size = TEXT_suffix.length();
        TEXT_separator_size = TEXT_separator.length();

        if (TEXT_map.length() > 0) {
            if (hasNamedField(TEXT_map) == false) {
                internalError(delimit(TEXT_map), "is not recognized as a TEXT field mapping array name");
            }
        }

        //
        // BYTE field initializations.
        //

        switch (BYTE_output) {
            case "BINARY":
                BYTE_map = "BINARY_BYTE_MAP";
                BYTE_digits_per_octet = 8;
                break;

            case "DECIMAL":
                BYTE_map = "DECIMAL_BYTE_MAP";
                BYTE_digits_per_octet = 3;
                break;

            case "EMPTY":
                if (TEXT_output.equals("EMPTY") == false) {
                    BYTE_map = "";
                    BYTE_digits_per_octet = 0;
                    DUMP_layout = DUMP_layout_default;
                    DUMP_field_flags &= ~BYTE_field_flag;
                } else {
                    userError("byte and text fields can't both be empty");
                }
                break;

            case "HEX-LOWER":
                BYTE_map = "HEX_LOWER_BYTE_MAP";
                BYTE_digits_per_octet = 2;
                break;

            case "HEX-UPPER":
                BYTE_map = "HEX_UPPER_BYTE_MAP";
                BYTE_digits_per_octet = 2;
                break;

            case "OCTAL":
                BYTE_map = "OCTAL_BYTE_MAP";
                BYTE_digits_per_octet = 3;
                break;

            case "XXD":
                BYTE_output = "HEX-LOWER";
                BYTE_map = "HEX_LOWER_BYTE_MAP";
                BYTE_digits_per_octet = 2;
                break;

            default:
                internalError("byte output", delimit(BYTE_output), "has not been implemented");
                break;
        }

        if (BYTE_map.length() > 0) {
            if (hasNamedField(BYTE_map) == false) {
                internalError(delimit(BYTE_map), "is not recognized as a BYTE field mapping array name");
            }
        }

        //
        // Unlike the bash version, counting the extra characters that print in the TEXT
        // field of the dump is trivial and locale independent, but only because we made
        // sure (in the option handling code) that all those characters are printable.
        //

        BYTE_prefix_size = BYTE_prefix.length();
        BYTE_suffix_size = BYTE_suffix.length();
        BYTE_separator_size = BYTE_separator.length();

        if (DUMP_record_length_limit > 0) {
            if (DUMP_record_length > DUMP_record_length_limit) {
                userError("requested record length", delimit(DUMP_record_length), "exceeds the internal buffer limit of", delimit(DUMP_record_length_limit), "bytes");
            }
        }
    }


    private static void
    initialize2_FieldWidths() {

        //
        // All we use BYTE_field_width for is to decide whether the BYTE field in the
        // dump's last record needs space padding, after the final byte, to make sure
        // its TEXT field starts in the correct column. It's only used in dumpAll(),
        // so that's where to look for more details.
        //
        // NOTE - even though the value stored in BYTE_field_width is correct, all we
        // really care about in this class is whether it's zero or not. A zero value
        // means padding isn't needed, which will happen when the BYTE or TEXT field
        // is empty, we're doing a single record or narrow dump, or there aren't any
        // missing bytes in the last record.
        //

        if (DUMP_record_length > 0) {
            if (BYTE_output.equals("EMPTY") || TEXT_output.equals("EMPTY") || DUMP_layout.equals("NARROW")) {
                BYTE_field_width = 0;
            } else {
                BYTE_field_width = DUMP_record_length*(BYTE_digits_per_octet + BYTE_separator_size) - BYTE_separator_size;
            }
        } else {
            BYTE_field_width = 0;
        }
    }


    private static void
    initialize3_Layout() {

        int padding;

        //
        // Different "layouts" give the user a little control over the arrangement of
        // each record's ADDR, BYTE, and TEXT fields. The currently supported layouts
        // are named "WIDE" and "NARROW". There are other possibilites, but these two
        // are easy to describe and feel like they should be more than sufficent. They
        // can be requested on the command line using the --wide or --narrow options.
        //
        // WIDE is the default layout and it generally resembles the way xxd organizes
        // its output - the ADDR, BYTE, and TEXT fields are printed next to each other,
        // and in that order, on the same line.
        //
        // The NARROW layout is harder and needs lots of subtle calculations to make
        // sure everything gets lined up properly. Basically NARROW layout prints the
        // ADDR and BYTE fields next to each other on the same line. The TEXT field is
        // printed by itself on the next line and what we have to do here is make sure
        // each character in the TEXT field is printed directly below the appropriate
        // byte in the BYTE field. The calculations are painful, so they've been split
        // into small steps that hopefully will be little easier to follow.
        //

        if (DUMP_layout.equals("NARROW")) {
            //
            // In this case, each TEXT field is supposed to be printed directly below
            // the corresponding BYTE field. Lots of adjustments will be required, but
            // the first step is make sure the TEXT and BYTE fields print on separate
            // lines by assigning a newline to the string that separates the BYTE field
            // from the TEXT field.
            //

            BYTE_field_separator = "\n";

            //
            // Figure out the number of spaces that need to be appended to the TEXT or
            // BYTE field indents to make the first byte and first character end up in
            // the same "column". The positioning of individual text characters within
            // the column will be addressed separately.
            //

            padding = BYTE_prefix_size - TEXT_prefix_size;
            if (padding > 0) {
                TEXT_indent = TEXT_indent + String.format("%" + padding + "s", "");
            } else if (padding < 0) {
                BYTE_indent = BYTE_indent + String.format("%" + (-padding) + "s", "");
            }

            //
            // Next, modify the separation between individual bytes in the BYTE field
            // or characters in the TEXT field so they all can be lined up vertically
            // when they're printed on separate lines.
            //

            padding = BYTE_digits_per_octet - TEXT_chars_per_octet + BYTE_separator_size - TEXT_separator_size;
            if (padding > 0) {
                TEXT_separator = TEXT_separator + String.format("%" + padding + "s", "");
                TEXT_separator_size = TEXT_separator.length();
            } else if (padding < 0) {
                BYTE_separator = BYTE_separator + String.format("%" + (-padding) + "s", "");
                BYTE_separator_size = BYTE_separator.length();
            }

            //
            // Adjust the TEXT field prefix by appending the number of spaces needed
            // to make sure the first character lines up right adjusted and directly
            // below the first displayed byte.
            //

            padding = BYTE_digits_per_octet - TEXT_chars_per_octet;
            if (padding > 0) {
                TEXT_prefix = TEXT_prefix + String.format("%" + padding + "s", "");
                //
                // Next line is missing from bash version - not important.
                //
                TEXT_prefix_size = TEXT_prefix.length();
            } else if (padding < 0) {
                internalError("chars per octet exceeds digits per octet");
            }

            //
            // If there's an address, adjust the TEXT field indent so all characters
            // line up vertically with the appropriate BYTE field bytes.
            //

            if (ADDR_output.equals("EMPTY") == false) {
                padding = ADDR_prefix_size + ADDR_digits + ADDR_suffix_size + ADDR_field_separator_size;
                if (padding > 0) {
                    TEXT_indent = TEXT_indent + String.format("%" + padding + "s", "");
                }
            }
        } else if (DUMP_layout.equals("WIDE") == false) {
            internalError("layout", delimit(DUMP_layout), "has not been implemented");
        }
    }


    private static void
    initialize4_Maps() {

        CharsetEncoder encoder = null;
        RegexManager   manager;
        String[]       groups;
        String         element;
        String         unexpanded = null;
        char           padding;
        int            codepoint;
        int            index;

        //
        // Makes sure the BYTE and TEXT field mapping arrays referenced by BYTE_map and
        // TEXT_map exist and, in the case of the TEXT field mapping array, is properly
        // initialized. After that it builds the addrMap and addrBuffer arrays, which
        // are the arrays that dumpFormattedAddress() uses to generate addresses without
        // using String.format().
        //

        if (BYTE_map.length() > 0) {
            if ((byteMap = (String[])getNamedStaticObject(BYTE_map)) == null) {
                internalError(delimit(BYTE_map), "is not a recognized byte mapping array name");
            }
        }

        if (TEXT_map.length() > 0) {
            if ((textMap = (String[])getNamedStaticObject(TEXT_map)) == null) {
                internalError(delimit(TEXT_map), "is not a recognized text mapping array name");
            }

            try {
                //
                // Java replaces code points that it can't encode with a single question mark.
                // Access to the encoder that String.valueOf() uses lets us intervene before
                // that replacement happens, but it's really not a big deal. Java's approach
                // is reasonable, but always using one question mark makes it a little harder
                // for us to notice encoding issues.
                //
                encoder = Charset.defaultCharset().newEncoder();
                unexpanded = (TEXT_unexpanded_string.length() > 0) ? TEXT_unexpanded_string : null;
            } catch (Exception e) {}

            if (DEBUG_unexpanded == false) {
                manager = new RegexManager();
                for (index = 0; index < textMap.length; index++) {
                    if ((element = textMap[index]) != null) {
                        //
                        // If element looks like a Unicode escape we need to deal with it. This
                        // will be where all of the escapes used in the TEXT field initializers
                        // are expanded.
                        //
                        // NOTE - we only need the four hex digits that represent code points,
                        // so their representation as Unicode escape sequences in the strings
                        // in TEXT field mapping array initializers is "useful overhead".
                        //
                        if ((groups = manager.matchedGroups(element, "^(.*)(\\\\u([0123456789abcdefABCDEF]{4}))$")) != null) {
                            codepoint = Integer.parseInt(groups[3], 16);
                            //
                            // Always go with Java's representation of bytes that it can't encode
                            // when unexpanded is null. Otherwise, encoder won't be null, so use
                            // it to check each codepoint and decide what to do.
                            //
                            if (unexpanded == null || encoder.canEncode((char)codepoint)) {
                                textMap[index] = groups[1] + String.valueOf((char)codepoint);
                            } else {
                                textMap[index] = unexpanded;
                            }
                        } else {
                            textMap[index] = element;
                        }
                    }
                }
            }
        }

        //
        // The bash version always generated the addresses that appear in the dump using
        // the printf builtin and ADDR_format. In Java, simple integer arithmetic and a
        // properly initialized buffer seem to build addresses a little faster than the
        // String.format() method. Any speed improvement needs a large file, dumped with
        // a relatively small record size, to be measured.
        //
        // NOTE - addresses are built by dumpFormattedAddress(), so that's where to look
        // for more details. If addrMap is null when this method returns, which currently
        // only happens when --debug=addresses was a command line option, String.format()
        // will be used to build all addresses.
        //

        if (DEBUG_addresses == false) {         // --debug=addresses sets it to true
            if (addrMap == null) {
                switch (ADDR_output) {
                    case "DECIMAL":
                        addrMap = new char[] {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'};
                        break;

                    case "HEX-LOWER":
                        addrMap = new char[] {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
                        break;

                    case "HEX-UPPER":
                        addrMap = new char[] {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F'};
                        break;

                    case "OCTAL":
                        addrMap = new char[] {'0', '1', '2', '3', '4', '5', '6', '7'};
                        break;
                }
            }

            if (addrMap != null) {
                //
                // Binary addresses aren't supported, so 21 (or 22) characters should be all
                // that's needed for octal addresses. Using Long.SIZE is overkill, but won't
                // impact performance and only wastes about 40 characters.
                //
                padding = (ADDR_padding.length() > 0) ? ADDR_padding.charAt(0) : ' ';
                addrBuffer = new char[Long.SIZE - 1];

                for (index = 0; index < addrBuffer.length; index++) {
                    addrBuffer[index] = padding;
                }
            }
        } else {
            addrMap = null;             // make sure String.format() is used
        }
    }


    private static void
    initialize5_Attributes() {

        RegexManager manager;
        String[]     byte_table;
        String[]     field_map;
        String[]     groups;
        String       field;
        String       layer;
        String       prefix;
        String       regex;
        String       suffix;
        int          index;
        int          flags;
        int          last;

        //
        // Applies attributes that were selected by command line options to the active
        // TEXT and BYTE field mapping arrays.
        //
        // NOTE - overriding command line selections when DEBUG_charclass_regex is set
        // is only done to help present the bytes selected by the character class when
        // the BYTE or TEXT field mapping arrays are dumped. Make sure every byte has
        // a forground or background color, by typing something like
        //
        //     ./bytedump-java --foreground=bright-green --text=caret --debug=bytemap,textmap --debug-charclass=punct /dev/null
        //
        // or
        //
        //     ./bytedump-java --background=red --text=unicode --debug=bytemap,textmap --debug-charclass=lower --background=red /dev/null
        //
        // and the bytes that are colored in the debugging dumps of the BYTE and TEXT
        // field mapping arrays should be an accurate represention of the bytes in the
        // hex list that's dumped for the selected charclass (e.g., punct or lower).
        //

        manager = new RegexManager();
        regex = DEBUG_charclass_regex;
        flags = DEBUG_charclass_flags;
        last = lastEncodedByte();

        for (String key : attributeTables.keySet()) {
            if ((byte_table = attributeTables.getTable(key)) != null) {
                if ((groups = manager.matchedGroups(key, "^(BYTE|TEXT)_(.+)$")) != null) {
                    field = groups[1];
                    layer = groups[2];
                    if (field.equals("BYTE")) {
                        field_map = byteMap;
                    } else {
                        field_map = textMap;
                    }
                    if (field_map != null) {
                        suffix = ANSI_ESCAPE.getOrDefault("RESET.attributes", "");
                        for (index = 0; index < byte_table.length; index++) {
                            if (index <= last) {
                                if (byte_table[index] != null && index < field_map.length) {
                                    //
                                    // Only apply attributes if DEBUG_charclass_regex wasn't set or
                                    // when the character with index as its code point matches that
                                    // regular expression.
                                    //
                                    if (regex == null || manager.matched(new String(Character.toChars(index)), regex, flags)) {
                                        prefix = ANSI_ESCAPE.getOrDefault(layer + "." + byte_table[index], "");
                                        if (prefix.length() > 0) {
                                            field_map[index] = prefix + field_map[index] + suffix;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }


    public static void
    main(String[] args) {

        Throwable cause;
        String    message;
        int       status;

        //
        // This method runs the program, basically by just calling the other methods that
        // do the real work. It's the method that's called when the java command launches
        // this class, which is what happens when the bytedump-java script is executed.
        //
        // Much of what's done here looks like it came from the bash implementation, but
        // what's happening in the catch block needs an explanation. If you've looked at
        // the source code for the bash version of bytedump you probably noticed lots of
        // explicit error checks. That's what bash makes you do, and because the goal in
        // this class is Java code that resembles the bash bytedump, it's a style that I
        // wanted to reproduce in this implementation.
        //
        // The first place to look, if you're trying to understand how errors are handled
        // in this class, is the Terminator.java file, and if you're familiar with how the
        // bash version handles errors you should see some similiarity. The most important
        // method in Terminator.java is named errorHandler. If you type something like
        //
        //     /errorHandler(
        //
        // in vim, you'll find errorHandler calls in the four error handling convenience
        // methods that are defined near the end of this class. They're all trivial, but
        // notice that "+exit" is an argument in each errorHandler call. Next look at the
        // last few lines in Terminator.errorHandler(). If it's supposed to exit, rather
        // than return, a method named terminate() is called and that's where the message
        // errorHandler built gets added to the Terminator.ExitException that ends up in
        // our catch block.
        //

        try {
            setup();
            options(args);
            initialize();
            debug();
            arguments(Arrays.copyOfRange(args, argumentsConsumed, args.length));
        } catch (Terminator.ExitException e) {
            if ((message = e.getMessage()) != null && message.length() > 0) {
                System.err.println(message);
            }
            if ((cause = e.getCause()) != null) {
                cause.printStackTrace();
            }

            if ((status = e.getStatus()) != 0) {
                System.exit(status);            // exit with a non-zero status
            }
        }
    }


    private static void
    options(String[] args) {

        RegexManager manager;
        String[]     groups;
        boolean      done;
        String       arg;
        String       attribute;
        String       length;
        String       number;
        String       optarg;
        String       selector;
        String       spacing;
        String       style;
        String       target;
        String       format_width;
        int          newlines;
        int          next;

        //
        // A long, but straightforward method that uses Java regular expressions and an instance
        // of the RegexManager class to process command line options. Everything was designed so
        // this method would "resemble" the option handling function in the bash implementation
        // of bytedump, and the RegexManager class is a fundamental part of the solution to that
        // puzzle. Take a look at the comments in RegexManager.java for all the details.
        //
        // Just like the bash version, main() needs to know how many arguments were consumed as
        // options. That number is stored in the argumentsConsumed class variable right before
        // this method returns, but only because that approach "resembles" how the bash version
        // does it. There are many other ways this could be handled in a Java program.
        //
        // NOTE - the options that set prefixes, separators, and suffixes let the user provide
        // strings that will appear in the dump we generate. That means the arguments of those
        // options are checked using a character class that accepts any character that the user
        // would consider printable.
        //

        manager = new RegexManager();           // for parsing the arguments
        done = false;                           // for early loop exit

        for (next = 0; next < args.length; next++) {
            arg = args[next];
            if ((groups = manager.matchedGroups(arg, "^(--[^=-][^=]*=)(.*)$")) != null) {
                target = groups[1];
                optarg = groups[2];
            } else if ((groups = manager.matchedGroups(arg, "^(--[^=-][^=]*)$")) != null) {
                target = groups[1];
                optarg = "";
            } else {
                target = arg;
                optarg = "";
            }

            switch (target) {
                case "--addr=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*(decimal|empty|hex|HEX|octal|xxd)[ \\t]*([:][ \\t]*([0]?[1-9][0-9]*)[ \\t]*)?$")) != null) {
                        //
                        // Implementation here, and in some of the other cases, could easily be
                        // simplified, but the goal in this version of the bytedump program is
                        // to make it "resemble" the bash implementation.
                        //
                        // NOTE - most Java programs would use defined String constants instead
                        // of String literals in code like this. This approach keeps everything
                        // much closer to the bash version, which was my main goal, even though
                        // it eliminates some pretty easy compile time error checking.
                        //
                        style = groups[1];
                        format_width = groups[3];
                        switch (style) {
                            case "decimal":
                                style = "DECIMAL";
                                break;

                            case "empty":
                                style = "EMPTY";
                                break;

                            case "hex":
                                style = "HEX-LOWER";
                                break;

                            case "HEX":
                                style = "HEX-UPPER";
                                break;

                            case "octal":
                                style = "OCTAL";
                                break;

                            case "xxd":
                                style = "XXD";
                                break;

                            default:
                                internalError("option", delimit(arg), "has not been completely implemented");
                                break;
                        }
                        ADDR_output = style;
                        if (format_width != null) {
                            ADDR_format_width = format_width;
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--addr-prefix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        ADDR_prefix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--addr-suffix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        ADDR_suffix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--background=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("BACKGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("BYTE_BACKGROUND"));
                            byteSelector(attribute, selector, attributeTables.getTable("TEXT_BACKGROUND"));
                        } else {
                            userError("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--byte=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*(binary|decimal|empty|hex|HEX|octal|xxd)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$")) != null) {
                        //
                        // Implementation here, and in some of the other cases, could easily be
                        // simplified, but the goal in this version of the bytedump program is
                        // to make it "resemble" the bash implementation.
                        //
                        style = groups[1];
                        length = groups[3];
                        switch (style) {
                            case "binary":
                                style = "BINARY";
                                break;

                            case "decimal":
                                style = "DECIMAL";
                                break;

                            case "empty":
                                style = "EMPTY";
                                break;

                            case "hex":
                                style = "HEX-LOWER";
                                break;

                            case "HEX":
                                style = "HEX-UPPER";
                                break;

                            case "octal":
                                style = "OCTAL";
                                break;

                            case "xxd":
                                style = "XXD";
                                break;

                            default:
                                internalError("option", delimit(arg), "has not been completely implemented");
                                break;
                        }
                        BYTE_output = style;
                        if (length != null) {
                            if ((DUMP_record_length = StringTo.unsignedInt(length)) < 0) {
                                rangeError("record length requested in option", delimit(optarg), "won't fit in a Java int");
                            }
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--byte-background=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("BACKGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("BYTE_BACKGROUND"));
                        } else {
                            userError("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--byte-foreground=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("FOREGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("BYTE_FOREGROUND"));
                        } else {
                            userError("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--byte-prefix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        BYTE_prefix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--byte-separator=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        BYTE_separator = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--byte-suffix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        BYTE_suffix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--copyright":
                    System.out.println(PROGRAM_COPYRIGHT);
                    Terminator.terminate();
                    break;

                case "--debug=":
                    for (String field : optarg.split(",")) {
                        field = field.trim();
                        switch (field) {
                            case "addresses":
                                DEBUG_addresses = true;
                                break;

                            case "background":
                                DEBUG_background = true;
                                break;

                            case "bytemap":
                                DEBUG_bytemap = true;
                                break;

                            case "fields":
                                DEBUG_fields = true;
                                break;

                            case "foreground":
                                DEBUG_foreground = true;
                                break;

                            case "textmap":
                                DEBUG_textmap = true;
                                break;

                            case "unexpanded":
                                DEBUG_unexpanded = true;
                                break;

                            default:
                                if (field.length() > 0) {
                                    userError("field", delimit(field), "in option", delimit(arg), "is not recognized");
                                }
                                break;
                        }
                    }
                    break;

                case "--debug-charclass=":
                    //
                    // Defines Java regular expressions that should build the hex byte lists that
                    // the byteSelector() method uses to implement "character class" tokens that
                    // are recognized in selector strings. I used them to generate the hex lists
                    // that you'll currently find in byteSelector() and you can do the same thing
                    // with this option - it's here if you want to check my work.
                    //
                    // NOTE - the hex list is generated by the debug() method. As a bonus, take a
                    // look at the comments and code in initialize5_Attributes() if you also want
                    // a quick visual display of the hex byte list.
                    //
                    DEBUG_charclass = optarg;
                    DEBUG_charclass_flags = RegexManager.UNICODE_CHARACTER_CLASS;
                    switch (optarg) {
                        case "alnum":
                            DEBUG_charclass_regex = "\\p{Alnum}";
                            break;

                        case "alpha":
                            DEBUG_charclass_regex = "\\p{Alpha}";
                            break;

                        case "blank":
                            DEBUG_charclass_regex = "\\p{Blank}";
                            break;

                        case "cntrl":
                            DEBUG_charclass_regex = "\\p{Cntrl}";
                            break;

                        case "digit":
                            DEBUG_charclass_regex = "\\p{Digit}";
                            break;

                        case "graph":
                            DEBUG_charclass_regex = "\\p{Graph}";
                            break;

                        case "lower":
                            DEBUG_charclass_regex = "\\p{Lower}";
                            break;

                        case "print":
                            DEBUG_charclass_regex = "\\p{Print}";
                            break;

                        case "punct":
                            DEBUG_charclass_regex = "\\p{Punct}";
                            break;

                        case "space":
                            DEBUG_charclass_regex = "\\p{Space}";
                            break;

                        case "upper":
                            DEBUG_charclass_regex = "\\p{Upper}";
                            break;

                        case "xdigit":
                            DEBUG_charclass_regex = "\\p{XDigit}";
                            break;

                        default:
                            userError("charcater class", delimit(optarg), "in option", delimit(arg), "is not recognized");
                            break;
                    }
                    break;

                case "--foreground=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("FOREGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("BYTE_FOREGROUND"));
                            byteSelector(attribute, selector, attributeTables.getTable("TEXT_FOREGROUND"));
                        } else {
                            userError("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--help":
                    help();
                    Terminator.terminate();
                    break;

                case "--length=":
                    if ((number = manager.matchedGroup(1, optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$")) != null) {
                        if ((DUMP_record_length = StringTo.unsignedInt(number)) < 0) {
                            rangeError("record length", delimit(number), "requested in option", delimit(arg), "won't fit in a Java int");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--length-limit=":
                    //
                    // Currently documented, but may remove that documentation.
                    //
                    if ((number = manager.matchedGroup(1, optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$")) != null) {
                        if ((DUMP_record_length_limit = StringTo.unsignedInt(number)) < 0) {
                            rangeError("record length limit", delimit(number), "requested in option", delimit(arg), "won't fit in a Java int");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--license":
                    System.out.println(PROGRAM_LICENSE);
                    Terminator.terminate();
                    break;

                case "--narrow":
                    DUMP_layout = "NARROW";
                    break;

                case "--read=":
                    if ((number = manager.matchedGroup(1, optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*$")) != null) {
                        if ((DUMP_input_read = StringTo.boundedInt(number, 0, DUMP_input_maxbuf, -1)) < 0) {
                            rangeError("byte count", delimit(number), "requested in option", delimit(arg), "must be an integer in the range [0, " + DUMP_input_maxbuf + "]");
                        }

                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--spacing=":
                    if ((spacing = manager.matchedGroup(1, optarg, "^[ \\t]*(1|single|2|double|3|triple)[ \\t]*$")) != null) {
                        switch (spacing)  {
                            case "1":
                            case "single":
                                DUMP_record_separator = "\n";
                                break;

                            case "2":
                            case "double":
                                DUMP_record_separator = "\n\n";
                                break;

                            case "3":
                            case "triple":
                                DUMP_record_separator = "\n\n\n";
                                break;

                            default:
                                internalError("option", delimit(arg), "has not been completely implemented");
                                break;
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--start=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$")) != null) {
                        if ((DUMP_input_start = StringTo.unsignedInt(groups[1])) >= 0) {
                            if (groups[3] != null) {
                                if ((DUMP_output_start = StringTo.unsignedInt(groups[3])) < 0) {
                                     rangeError("address argument", delimit(groups[3]), "in option", delimit(arg), "wont't fit in a Java int");
                                }
                            } else {
                                DUMP_output_start = DUMP_input_start;
                            }
                        } else {
                            rangeError("skip argument", delimit(groups[1]), "in option", delimit(arg), "wont't fit in a Java int");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--text=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*(ascii|caret|empty|escape|unicode|xxd)[ \\t]*([:][ \\t]*([1-9][0-9]*|0[xX][0-9a-fA-F]+|0[0-7]*)[ \\t]*)?$")) != null) {
                        //
                        // Implementation here, and in some of the other cases, could easily be
                        // simplified, but the goal in this version of the bytedump program is
                        // to make it "resemble" the bash implementation.
                        //
                        style = groups[1];
                        length = groups[3];
                        switch (style) {
                            case "ascii":
                                style = "ASCII";
                                break;

                            case "caret":
                                style = "CARET";
                                break;

                            case "empty":
                                style = "EMPTY";
                                break;

                            case "escape":
                                style = "CARET_ESCAPE";
                                break;

                            case "unicode":
                                style = "UNICODE";
                                break;

                            case "xxd":
                                style = "XXD";
                                break;

                            default:
                                internalError("option", delimit(arg), "has not been completely implemented");
                                break;
                        }
                        TEXT_output = style;
                        if (length != null) {
                            if ((DUMP_record_length = StringTo.unsignedInt(length)) < 0) {
                                rangeError("record length requested in option", delimit(optarg), "won't fit in a Java int");
                            }
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--text-background=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("BACKGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("TEXT_BACKGROUND"));
                        } else {
                            userError("background attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--text-foreground=":
                    if ((groups = manager.matchedGroups(optarg, "^[ \\t]*([a-zA-Z]+([-][a-zA-Z]+)*)[ \\t]*([:][ \\t]*(.*))?$")) != null) {
                        attribute = groups[1];
                        selector = (groups[3] != null) ? groups[4] : "0x(00-FF)";
                        if (ANSI_ESCAPE.containsKey("FOREGROUND." + attribute)) {
                            byteSelector(attribute, selector, attributeTables.getTable("TEXT_FOREGROUND"));
                        } else {
                            userError("foreground attribute", delimit(attribute), "in option", delimit(arg), "is not recognized");
                        }
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "is not recognized");
                    }
                    break;

                case "--text-prefix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        TEXT_prefix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--text-suffix=":
                    if (manager.matched(optarg, "^\\p{Print}*$", RegexManager.UNICODE_CHARACTER_CLASS)) {
                        TEXT_suffix = optarg;
                    } else {
                        userError("argument", delimit(optarg), "in option", delimit(arg), "contains unprintable characters");
                    }
                    break;

                case "--version":
                    System.out.println(PROGRAM_VERSION);
                    Terminator.terminate();
                    break;

                case "--wide":
                    DUMP_layout = "WIDE";
                    break;

                case "-":
                    done = true;
                    break;

                case "--":
                    done = true;
                    next++;
                    break;

                default:
                    done = true;
                    if (target.startsWith("-")) {
                        userError("invalid option", delimit(arg));
                    }
                    break;
            }

            if (done) {
                break;
            }
        }

        argumentsConsumed = next;
    }


    private static void
    setup() {

        //
        // This is where initialization that needs to happen before the command line
        // are processed could be done. Java's a much better language than bash, and
        // as things stand there's nothing this method needs to do.
        //

    }

    ///////////////////////////////////
    //
    // Error Methods
    //
    ///////////////////////////////////

    private static void
    internalError(String... args) {

        //
        // Error handling convenience method.
        //

        Terminator.errorHandler(
            "-prefix=" + PROGRAM_NAME,
            "-tag=InternalError",
            "-info=location",
            "+exit",
            "+frame",
            "--",
            String.join(" ", Arrays.copyOfRange(args, 0, args.length))
        );
    }


    private static void
    javaError(String... args) {

        //
        // Error handling convenience method.
        //

        Terminator.errorHandler(
            "-prefix=" + PROGRAM_NAME,
            "-tag=JavaError",
            "-info=location",
            "+exit",
            "+frame",
            "--",
            String.join(" ", Arrays.copyOfRange(args, 0, args.length))
        );
    }


    private static void
    rangeError(String... args) {

        //
        // Error handling convenience method.
        //

        Terminator.errorHandler(
            "-prefix=" + PROGRAM_NAME,
            "-tag=RangeError",
            "-info",
            "+exit",
            "+frame",
            "--",
            String.join(" ", Arrays.copyOfRange(args, 0, args.length))
        );
    }


    private static void
    userError(String... args) {

        //
        // Error handling convenience method.
        //

        Terminator.errorHandler(
            "-prefix=" + PROGRAM_NAME,
            "-tag=Error",
            "-info",
            "+exit",
            "+frame",
            "--",
            String.join(" ", Arrays.copyOfRange(args, 0, args.length))
        );
    }

    ///////////////////////////////////
    //
    // Helper Methods
    //
    ///////////////////////////////////

    private static ByteArrayInputStream
    byteLoader(InputStream input, int limit)

        throws IOException

    {

        ByteArrayOutputStream output;
        byte[]                buffer;
        int                   count;
        int                   total;

        //
        // Reads up to limit bytes from input into a ByteArrayOutputStream, stopping when
        // limit bytes are read or when input.read() returns a number that's not positive.
        // The collected bytes are then copied into a ByteArrayInputStream that's returned
        // to the caller, where it can be used to replace the original InputStream.
        //
        // NOTE - this method is only used support reading a fixed, but limited, number of
        // bytes from an input file that's triggered by the --read option.
        //

        output = new ByteArrayOutputStream();
        buffer = new byte[4096];
        for (total = 0; total < limit; total = output.size()) {
            if ((count = input.read(buffer)) > 0) {
                output.write(buffer, 0, Math.min(count, limit - total));
            } else {
                break;
            }
        }
        return(new ByteArrayInputStream(output.toByteArray()));
    }


    private static String
    delimit(int arg) {

        return(delimit(String.valueOf(arg)));
    }


    private static String
    delimit(String... args) {

        //
        // A trivial method that joins it's arguments using one space, surrounds that
        // string with double quotes, and returns it to the caller. It's currently only
        // used to visually isolate the cause of an error from its explanation in error
        // messages.
        //

        return("\"" + StringTo.joiner(" ", args) + "\"");
    }


    private static Field[]
    getDeclaredFields() {

        Class<?> clazz;
        Field[]  fields = null;

        if ((clazz = getThisClass()) != null) {
            fields = clazz.getDeclaredFields();
        }

        return(fields);
    }


    private static Field
    getNamedField(String name) {

        Class<?> clazz;
        Field    field = null;

        if (name != null) {
            if ((clazz = getThisClass()) != null) {
                try {
                    field = clazz.getDeclaredField(name);
                } catch (ReflectiveOperationException e) {}
            }
        }

        return(field);
    }


    private static InputStream
    getNamedResourceAsStream(String name) {

        InputStream stream = null;
        Class<?>    clazz;

        if (name != null) {
            if ((clazz = getThisClass()) != null) {
                stream = clazz.getResourceAsStream(name);
            }
        }

        return(stream);
    }


    private static Object
    getNamedStaticObject(String name) {

        Object obj = null;
        Field  field;

        if ((field = getNamedField(name)) != null) {
            if (Modifier.isStatic(field.getModifiers())) {
                try {
                    obj = field.get(null);
                } catch (ReflectiveOperationException e) {}
            }
        }

        return(obj);
    }


    private static String
    getSystemProperty(String key) {

        return(getSystemProperty(key, null));
    }


    private static String
    getSystemProperty(String key, String value) {

        if (key != null && key.length() > 0) {
            value = System.getProperty(key, value);
        }

        return(value);
    }


    private static Class<?>
    getThisClass() {

        //
        // Getting the class that "owns" a static method (from that method) is tricky.
        // What's done here uses an anonymous class and reflection to grab it, rather
        // than trying to find it in the current thread's stack trace (which is how I
        // got that class when I started - quite a while ago).
        //
        // NOTE - hardcoding the class name is another possibility, but I didn't find
        // that approach attractive, mostly because it wasn't hard to imagine another
        // Java implementation of bytedump that could benefit by "borrowing" chunks of
        // code from this class. Definitely not a big deal, but this is really easy.
        //

        return(new Object(){}.getClass().getEnclosingClass());          // an anonymous class
    }


    private static String
    getThisClassName() {

        return(getThisClass().getName());
    }


    private static boolean
    hasNamedField(String name) {

        return(getNamedField(name) != null);
    }


    private static int
    lastEncodedByte() {

        return(Charset.defaultCharset().name().equals("US-ASCII") ? 127 : 255);
    }


    private static boolean
    pathIsDirectory(String path) {

        boolean result = false;

        if (path != null) {
            try {
                result = (new File(path)).isDirectory();
            } catch (SecurityException e) {}
        }

        return(result);
    }


    private static boolean
    pathIsReadable(String path) {

        boolean result = false;

        if (path != null) {
            try {
                result = (new File(path)).canRead();
            } catch (SecurityException e) {}
        }

        return(result);
    }
}

