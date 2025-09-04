/*
 * Copyright (C) 2025 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)
 * SPDX-License-Identifier: MIT
 */

/*
 * There's no package statement in this source file because I didn't want to impose
 * a directory structure on the source files used to build the Java version of the
 * bytedump application.
 *
 * NOTE - if you add a package statement and reorganize things you undoubtedly will
 * also have to modify the makefile. If I have time and there's any interest, I may
 * provide an example makefile that deals with Java packages.
 */

/*
 * A pretty simple collection of static methods that operate on Strings. The methods
 * that convert numeric string literals to Java ints or longs and make sure they fit
 * in a specific range can be useful when you're dealing with numbers set by command
 * line options. Methods that combine strings in various ways can be useful when you
 * want to make sure null arguments are ignored, rather than translated to "null" and
 * included in the String that's returned to the caller.
 *
 * NOTE - in Java source files I only use block style comments, like the one you're
 * reading right now, outside class definitions, because that means they're usually
 * available for temporarily commenting out one or more lines of Java code.
 */

public abstract
class StringTo {

    ///////////////////////////////////
    //
    // StringTo Methods
    //
    ///////////////////////////////////

    public static int
    boundedInt(String literal, int min, int max, int fail)  {

        return((int)boundedLong(literal, min, max, fail));
    }


    public static long
    boundedLong(String literal, long min, long max, long fail)  {

        long value;

        //
        // Tries to convert a string that's supposed to be a literal representation of a
        // decimal, hex, octal, or binary integer to a long. If the conversion works and
        // the result is in the closed interval [min, max] that's our answer, otherwise
        // whatever the caller handed us in fail is what we return.
        //
        // NOTE - using regular expressions and the RegexManager class to pick the radix
        // that parseLong() expects as its second argument. There are many alternatives
        // if you don't like this approach.
        //

        try {
            if (RegexManager.getMatched(literal, "^[-+]?[0]+$")) {
                value = 0;
            } else if (RegexManager.getMatched(literal, "^[-+]?[123456789][0123456789]*$")) {
                value = Long.parseLong(literal, 10);
            } else if (RegexManager.getMatched(literal, "^[-+]?0[xX][0123456789abcdefABCDEF]+$")) {
                value = Long.parseLong(literal.replaceFirst("0[xX]", ""), 16);
            } else if (RegexManager.getMatched(literal, "^[-+]?0[01234567]+$")) {
                value = Long.parseLong(literal, 8);
            } else if (RegexManager.getMatched(literal, "^[-+]?0[bB][01]+$")) {
                value = Long.parseLong(literal.replaceFirst("0[bB]", ""), 2);
            } else {
                //
                // This ends up in the outer catch block.
                //
                throw(new NumberFormatException());
            }
            if (value < min || value > max) {
                value = fail;
            }
        } catch (NumberFormatException e) {
            value = fail;
        }

        return(value);
    }


    public static String
    connector(String... args) {

        String result = null;
        String separator;
        String str;
        int    index;
        int    length;

        //
        // Returns a string that's built by joining the non-null strings at even indices
        // in args, but only after the string at the odd index that preceeds each one is
        // used to separate it from the string that's already been constructed. Separator
        // strings (the ones at odd indices) are only used when they're not null and when
        // the next string in the args array is defined, not null or empty, and the result
        // that's already built also isn't null or empty.
        //
        // NOTE - this method probably isn't used and hasn't been well tested. Decided to
        // leave it in for now, but that may eventually change.
        //

        if (args != null) {
            if ((length = args.length) > 0) {
                result = args[0];
                for (index = 1; index < length - 1; index += 2) {
                    separator = args[index];
                    str = args[index + 1];
                    if (result == null) {
                        result = str;
                    } else if (str != null && str.length() > 0) {
                        result += ((separator != null) ? separator : "") + str;
                    }
                }
            }
        }

        return(result);
    }


    public static String
    joiner(String delimiter, String... elements) {

        String result = null;

        //
        // Basically an implementation of Java's String.join() that's been restricted to
        // String arguments, forced to skip null (or empty) String elements, and told to
        // use "" if the delimiter is null.
        //

        if (elements != null) {
            delimiter = (delimiter != null) ? delimiter : "";
            for (String str : elements) {
                if (str != null && str.length() > 0) {
                    if (result == null || result.length() == 0) {
                        result = str;
                    } else {
                        result += delimiter + str;
                    }
                }
            }
        }

        return(result);
    }


    public static String
    literal(String source, boolean quote) {

        StringBuilder buffer;

        //
        // Add backslash escapes, where required, to make sure individual characters in
        // source appear if those escaped characters are used in a Java String literal.
        // If the quote argument is true, the string that's returned to the caller will
        // be surrounded by double quotes.
        //
        // NOTE - this method was originally used in error handlers to isolate a string
        // that triggered a problem from the rest fo the error message that explains the
        // mistake. Surrounding the problem string with double quotes seems better than
        // trying to turn it into a Java String literal, so this method is hardly used.
        //

        buffer = new StringBuilder();

        if (source != null) {
            for (char c : source.toCharArray()) {
                switch (c) {
                    case '"':
                        buffer.append("\\\"");
                        break;

                    case '\\':
                        buffer.append("\\\\");
                        break;

                    case '\n':
                        buffer.append("\\n");
                        break;

                    case '\t':
                        buffer.append("\\t");
                        break;

                    case '\r':
                        buffer.append("\\r");
                        break;

                    case '\f':
                        buffer.append("\\f");
                        break;

                    default:
                        buffer.append(c);
                        break;
                }
            }
        }

        return(quote ? "\"" + buffer.toString() + "\"" : buffer.toString());
    }


    public static int
    nonNegativeInt(String literal) {

        return(boundedInt(literal, 0, Integer.MAX_VALUE, -1));
    }


    public static int
    positiveInt(String literal) {

        return(boundedInt(literal, 1, Integer.MAX_VALUE, -1));
    }


    public static int
    unsignedInt(String literal)  {

        //
        // No unsigned types in Java so Integer.MAX_VALUE is still the upper bound.
        //

        return(boundedInt(literal, 0, Integer.MAX_VALUE, -1));
    }
}

