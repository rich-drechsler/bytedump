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

import java.util.HashMap;
import java.util.TreeSet;

/*
 * This HashMap extension is responsible for creating and managing the 256 element
 * String arrays that versions of bytedump use to remember attributes, like colors,
 * that command line options assign to the BACKGROUND and FOREGROUND layers of the
 * bytes that are displayed in the dump's BYTE and TEXT fields.
 *
 * The constructor is called with a list of keys that will be recognized as names
 * of the tables that are being managed. Hand one of those names to getTable() and
 * you get the String array that's associated with that name. That's basically all
 * there is to this class - whatever goes in those tables and how it ends up being
 * used makes no difference here.
 *
 * NOTE - in Java source files I only use block style comments, like the one you're
 * reading right now, outside class definitions, because that means they're usually
 * available for temporarily commenting out one or more lines of Java code.
 */

public
class AttributeTables extends HashMap<String, String[]> {

    private static final int TABLE_SIZE = 256;

    //
    // This is where the keys handed to the constructor are saved.
    //

    private TreeSet<String> registeredKeys = new TreeSet<>();

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
    AttributeTables(String... keys) {

        //
        // Arguments are saved in registeredKeys and end up being the only ones getTable()
        // accepts when it's asked to return the table (i.e., the 256 element String array)
        // that's associated with a registered key. At least one argument is required and
        // none of them can be null. Tables all start as null and they're only turned into
        // usable tables by getTable().
        //

        if (keys.length > 0 ) {
            for (String key : keys) {
                if (key != null) {
                    put(key, null);                 // tables all start out null
                    registeredKeys.add(key);
                } else {
                    throw(new NullPointerException("null keys are not allowed"));
                }
            }
        } else {
            throw(new IllegalArgumentException("constructor requires at least one argument"));
        }
    }

    ///////////////////////////////////
    //
    // AttributeTables Methods
    //
    ///////////////////////////////////

    public void
    dumpTable(String key, String prefix) {

        String[] table;
        String   value;
        String   elements;
        String   separator;
        int      count;
        int      index;

        //
        // This method can reproduce the "debugging" output that the original bash version
        // of bytedump produced when it was asked to display "background" or "foreground"
        // attributes that command line options assigned to individual bytes displayed in
        // the dump's BYTE or TEXT fields.
        //
        // NOTE - can't tell how many non-null entries are in each array until we've had
        // a chance to count them, so the info about each non-null byte is collected in a
        // string that's written to standard error after that counting is complete.
        //

        if ((table = get(key)) != null) {
            count = 0;
            prefix = (prefix != null) ? prefix : "";
            elements = "";
            separator = "";
            for (index = 0; index < table.length; index++) {
                if ((value = table[index]) != null) {
                    elements += String.format("%s%s  %5s=%s", separator, prefix, "[" + index + "]", "\"" + value + "\"");
                    separator = "\n";
                    count++;
                }
            }
            if (count > 0) {
                System.err.println(prefix + key + "[" + count + "]:");
                System.err.println(elements);
                System.err.println();
            }
        }
    }


    public String[]
    getTable(String key) {

        String[] table;

        //
        // Returns the table that is (or soon will be) associated with key, but only if
        // key is in registeredKeys. The table is created and added to this HashMap if
        // it's not there yet, which should only happen on the first request for key's
        // table.
        //

        if (registeredKeys.contains(key)) {
            if (key != null) {
                if ((table = get(key)) == null) {
                    table = new String[TABLE_SIZE];
                    put(key, table);
                }
            } else {
                throw(new NullPointerException());
            }
        } else {
            throw(new IllegalArgumentException(key + " is not a key that was registered by the constructor."));
        }

        return(table);
    }
}

