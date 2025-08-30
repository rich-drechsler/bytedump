/*
 * Copyright (C) 2025 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)
 * SPDX-License-Identifier: MIT
 */

/*
 * There's no package statement in this source file because I didn't want to impose
 * a directory structure on the files used to build the Java version of the bytedump
 * application. If you add a package statement and reorganize things you undoubtedly
 * will also have to modify the makefile.
 */

import java.util.HashMap;

/*
 * A HashMap extension that maps Strings to Strings and defines a constructor that
 * accepts a variable number of String arguments. At one point there was much more
 * to this class, but now the varargs constructor is about all that's left, and only
 * because it can build a StringMap in a way that resembles how the bash version of
 * bytedump declared and initialized one large associative array.
 *
 * NOTE - in Java source files I only use block style comments, like the one you're
 * reading right now, outside class definitions, because that means they're usually
 * available for temporarily commenting out one or more lines of Java code.
 */

public
class StringMap extends HashMap<String, String> {

    //
    // To make javac happy.
    //

    private static final long serialVersionUID = 1L;

    ///////////////////////////////////
    //
    // Constructors
    //
    ///////////////////////////////////

    public
    StringMap(String... pairs) {

        putPairs(pairs);
    }

    ///////////////////////////////////
    //
    // Private Methods
    //
    ///////////////////////////////////

    private void
    putPairs(String... pairs) {

        int index;
        int length;

        //
        // HashMap allows null as a key or value, so right now we do too.
        //

        if (pairs != null) {
            if ((length = pairs.length) > 0) {
                for (index = 0; index < length; index += 2) {
                    put(
                        pairs[index],
                        (index < length - 1) ? pairs[index + 1] : null
                    );
                }
            }
        }
    }
}

