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
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.regex.PatternSyntaxException;
import java.util.TreeSet;

/*
 * This class was used to help convert the bash implementation of bytedump to a Java
 * version. My goal, when I eventually started working on the conversion, was a Java
 * class (currently ByteDump) that resembled the bytedump bash script closely enough
 * that understanding one implementation would be useful if you decided to dig into
 * the other. Regular expressions pop up all over the place in the bash version of
 * bytedump and they're supported by both languages, but their capabilities and the
 * way they're typically used in programs can look very different. Trying to smooth
 * out some of the "structural" differences is why this class was built.
 *
 * Matching a string against a bash regular expression is an operation that returns
 * an integer that reflects what happened and, as a bonus, successful matches also
 * populate the BASH_REMATCH array with all of the matched subexpressions. It leads
 * to a style in the bash bytedump script where regular expressions are matched in
 * an if statement, the true branch handles a successful match, often using strings
 * stored in BASH_REMATCH, and the false branch is responsible for all unsuccessful
 * matches.
 *
 * Reproducing that "style" in the Java conversion would be useful, but didn't seem
 * possible without a new method or a new class, like this one, sitting between the
 * application and Java's Pattern and Matcher classes. In fact, a method that takes
 * at least two arguments (the target and regular expression strings) and returns a
 * String array filled with the matched groups on a successful match, or null if the
 * match fails, probably could (in a single method call) replicate what happens when
 * a bash script uses a regular expression.
 *
 * That would preserve the overall "structure" of the regular expression code used
 * in the two versions, but hiding Java's Pattern and Matcher classes from users is
 * an approach with consequences that this class has to address. Regular expressions
 * in Java are tiny little programs, written in a cryptic language that's encoded in
 * a Java string. Even though it's often hard to believe, the "language" that those
 * little programs are written in is primarily for people, not computers - regular
 * expression strings always have to be translated into a different format before
 * they can be efficiently used to match target strings.
 *
 * That translation is usually called compilation. It happens behind the scenes in
 * bash scripts, but in Java, applications are responsible for compiling a regular
 * expression, and it's done using one of the public compile() methods defined in
 * the Pattern class. Adopting bash's regular expression approach means that this
 * class (rather than ByteDump) will have to be responsible for the compilation of
 * regular expression strings that are passed as arguments to its public methods.
 *
 * If you're curious about what happens when regular expressions are compiled, take
 * a quick look at the source code for Java's Pattern class. It's available online
 * at
 *
 *     https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/regex/Pattern.java
 *
 * or in the src.zip file that's distributed with most (perhaps all) JDK releases.
 * Following all the compilation details isn't important, but convincing yourself
 * that it might not be a trivial operation is probably worth a quick look.
 *
 * Every regular expression in a Java program has to be compiled before it's used,
 * and as far as I know, calling Pattern.compile() (while the program is running)
 * at least once for each regular expression, is the only reasonable way to do it.
 * When it succeeds, the compiled regular expression is encapsulated in a Pattern
 * class that's returned to the caller. As long as we hang on to one reference to
 * that Pattern, we shouldn't have to recompile the regular expression when we're
 * asked to use it again.
 *
 * Once you have that compiled pattern, you use its matcher() method to create a
 * Matcher class instance that matches a CharSequence (which for our purposes is
 * always a String) against that compiled regular expression. A quick look at the
 * matcher() method definition in Java's Pattern.java class file should convince
 * you that it's not an expensive operation, particularly when compared to regular
 * expression compilation. With that in mind, I decided to keep things simple and
 * create a new Matcher instance (from an existing Pattern) whenever we need one.
 *
 * Hiding Java's Pattern and Matcher classes from an application, but doing it in
 * a way that gives the application some control over the recompilation of regular
 * expressions, means implementing a simple caching mechanism that can be used to
 * recover compiled Patterns. Caching really isn't expensive, so remembering every
 * successfully compiled regular expression would not be unreasonable. However, I
 * wanted applications to have the final say, so right now instance methods always
 * cache newly created Patterns, while static methods never do. The public instance
 * methods named
 *
 *     matched()
 *     matchedGroups()
 *     matchedGroup()
 *
 * and their static counterparts
 *
 *     getMatched()
 *     getMatchedGroups()
 *     getMatchedGroup()
 *
 * are the methods that were specifically designed for converting the bash bytedump
 * implementation to Java. Matcher classes created by any of those methods are never
 * saved.
 *
 * NOTE - in all methods that take the target string and regular expression string
 * as arguments, the target always preceeds the regular expression in the argument
 * list. It's the order they "appear" in bash regular expressions and that's really
 * why I picked it.
 *
 * NOTE - my guess is this file, Terminator.java, and maybe StringTo.java are the
 * only class files that might be useful in completely unrelated Java applications.
 * Feel free to grab them if you want. Terminator.java and StringTo.java currently
 * use this class, but removing that dependence would not be difficult.
 *
 * NOTE - in Java source files I only use block style comments, like the one you're
 * reading right now, outside class definitions, because that means they're usually
 * available for temporarily commenting out one or more lines of Java code.
 */

public
class RegexManager {

    //
    // Public copies of the Pattern class compilation flags. They're used in this class
    // to build FLAGS_MASK and they can be combined by applications to build flags that
    // are accepted by a few public methods and used to control how regular expressions
    // are compiled.
    //
    // NOTE - replicating the Pattern class compilation flags here means code that uses
    // this class won't have to import (or explicitly reference) Java's Pattern class.
    //

    public final static int CANON_EQ = Pattern.CANON_EQ;
    public final static int CASE_INSENSITIVE = Pattern.CASE_INSENSITIVE;
    public final static int COMMENTS = Pattern.COMMENTS;
    public final static int DOTALL = Pattern.DOTALL;
    public final static int LITERAL = Pattern.LITERAL;
    public final static int MULTILINE = Pattern.MULTILINE;
    public final static int UNICODE_CASE = Pattern.UNICODE_CASE;
    public final static int UNICODE_CHARACTER_CLASS = Pattern.UNICODE_CHARACTER_CLASS;
    public final static int UNIX_LINES = Pattern.UNIX_LINES;

    public final static int FLAGS_MASK = (CANON_EQ|CASE_INSENSITIVE|COMMENTS|DOTALL|LITERAL|MULTILINE|UNICODE_CASE|UNICODE_CHARACTER_CLASS|UNIX_LINES);
    public final static int FLAGS_DEFAULT = 0;

    //
    // A HashMap that instances of this class use to remember the compiled versions
    // of regular expressions, which end up as instances of Java's Pattern class. All
    // instance methods that have "cache" in their names are closely connected to the
    // cache. Static methods don't do any caching.
    //

    private HashMap<String, Pattern> regexCache = new HashMap<>();

    //
    // By default, regular expressions are compiled and then cached whenever instance
    // methods need a Pattern for a matching operation. It's convenient and efficient,
    // and usually happens automatically whenever compiledRegex() is called, but delay
    // also has a downside. Syntax errors can hide in regular expressions and the only
    // way to be certain that a non-trivial regular expression is valid (but maybe not
    // correct) is to compile it.
    //
    // The cacheLoader() instance method (or the constructor that calls it) is an easy
    // way to force the compilation of a bunch of regular expressions. If you want to
    // be even stricter set lockedCache to true, and then any regular expression used
    // by an instance method must be compiled and cached by cacheLoader(). Permanently
    // changing the default to true is not something I would recommend, but doing it
    // as a temporary hack isn't unreasonable.
    //
    // NOTE - programs that use this class can change lockedCache by passing a boolean
    // as the last argument in a cacheLoader() or constructor call.
    //
    // NOTE - mistakes in non-trivial regular expressions are so common that most of
    // them should be checked for syntax errors, which is easy, and carefully tested
    // for mistakes in logic, which is harder. If you've tested all your non-trivial
    // regular expressions then you know they compile, so delaying their compilation
    // until a program really needs them makes lots of sense, and that's exactly what
    // happens when lockedCache is false.
    //

    private boolean lockedCache = false;        // true => cacheLoader() is in control

    //
    // The key associated with a compiled regular expression in the cache is built by
    // separating the compilation flags and the regular expression with KEY_SEPARATOR.
    // It's a string that shouldn't be null or empty, or contain digits that could be
    // confused with the compilation flags.
    //

    private static final String KEY_SEPARATOR = ":";

    ///////////////////////////////////
    //
    // Constructors
    //
    ///////////////////////////////////

    public
    RegexManager(Object... args) {

        //
        // Compiles and caches a bunch of regular expressions. Arguments stored in args[]
        // are Strings that are regular expressions, or Integers that are the flags used
        // when regular expressions are compiled. In addition, the last argument can also
        // be a Boolean that's assigned to lockedCache, which ends up determining exactly
        // where this RegexManager instance can compile and cache regular expressions. If
        // you want more details, take a look at cacheLoader().
        //
        // NOTE - Java's autoboxing, which is managed by javac, means that int or boolean
        // arguments are converted to Integer or Boolean Objects before they're included
        // in args.
        //

        cacheLoader(args);
    }

    ///////////////////////////////////
    //
    // RegexManager Methods
    //
    ///////////////////////////////////

    public int
    cacheCount() {

        return(regexCache.size());
    }


    public void
    cacheDump() {

        cacheDump("", "");
    }


    public void
    cacheDump(String left, String right) {

        Pattern pattern;
        String  regex;
        int     flags;

        //
        // This method was written to help with debugging when caching was added to this
        // class. There's a small chance it still has some value, but it eventually may
        // disappear. The left and right arguments are only used to surround the HashMap
        // key in the debugging output. They're really only useful when there's explicit
        // whitespace on either end of a regular expression.
        //

        if (regexCache != null) {
            System.err.println("regexCache[" + regexCache.size() + "][" + (lockedCache ? "LOCKED" : "UNLOCKED") + "]:");
            for (String key : new TreeSet<>(regexCache.keySet())) {
                System.err.println("    " + (left != null ? left : "") + key + (right != null ? right : ""));
                regex = cacheKeyRegex(key);
                flags = cacheKeyFlags(key);
                if ((pattern = regexCache.get(key)) != null) {
                    System.err.println("        COMPILED=true, FLAGS=" + flags + ", REGEX=" + left + regex + right);
                    if (flags != pattern.flags()) {
                        System.err.println("          **MISMATCHED FLAGS=" + pattern.flags());
                    }
                    if (regex.equals(pattern.pattern()) == false) {
                        System.err.println("          **MISMATCHED REGEX=" + pattern.pattern());
                    }
                } else {
                    System.err.println("        COMPILED=false, FLAGS=" + flags + ", REGEX=" + left + regex + right);
                }
            }
        } else {
            System.err.println("regexCache=null");
        }
    }


    public void
    cacheLoader(Object... args) {

        Object arg;
        String regex;
        String key;
        int    flags;
        int    index;

        //
        // Compiles and caches a bunch of regular expressions. Arguments stored in args[]
        // are Strings that are regular expressions, or Integers that are the flags used
        // when regular expressions are compiled. In addition, the last argument can also
        // be a Boolean that's assigned to lockedCache, which ends up determining exactly
        // where this RegexManager instance can compile and cache regular expressions.
        //
        // The value represented by each Integer argument is saved in the flags variable.
        // Each String argument is assumed to be a regular expression that's compiled and
        // cached using the last value that was assigned to flags. All null arguments are
        // ignored.
        //
        // NOTE - Java's autoboxing, which is managed by javac, means that int or boolean
        // arguments are converted to Integer or Boolean Objects before they're included
        // in args.
        //

        flags = FLAGS_DEFAULT;
        for (index = 0; index < args.length; index++) {
            arg = args[index];
            if (arg != null) {
                if (arg instanceof Integer) {
                    flags = ((Integer)arg).intValue() & FLAGS_MASK;
                } else if (arg instanceof String) {
                    regex = (String)arg;
                    key = cacheKey(regex, flags);
                    if (regexCache.containsKey(key) == false) {
                        regexCache.put(key, getCompiledRegex(regex, flags));
                    }
                } else if (arg instanceof Boolean) {
                    if (index == args.length - 1) {             // last argument?
                        lockedCache = ((Boolean)arg).booleanValue();
                    } else {
                        throw(new IllegalArgumentException("boolean to set locked state of the cache must be the last argument"));
                    }
                } else {
                    throw(new IllegalArgumentException("argument " + arg + " isn't a regular expression string or integer compilation flags"));
                }
            }
        }
    }


    public static boolean
    checkSyntax(String regex) {

        return(checkSyntax(regex, FLAGS_DEFAULT, false));
    }


    public static boolean
    checkSyntax(String regex, boolean silent) {

        return(checkSyntax(regex, FLAGS_DEFAULT, silent));
    }

    public static boolean
    checkSyntax(String regex, int flags) {

        return(checkSyntax(regex, flags, false));
    }

    public static boolean
    checkSyntax(String regex, int flags, boolean silent) {

        boolean compiled = false;

        //
        // Might occasionally be useful if you just want to make sure there aren't any
        // syntax errors in a regular expression. This is a static method, which means
        // there's no caching or any other way to use a successfully compiled regular
        // expression. Syntax errors are always caught - the exception's error message
        // is written to System.err and false is returned, which is supposed to let the
        // caller decide what to do.
        //
        // NOTE - an easy option, if there are a bunch of regular expressions that you
        // want to check, is to use the constructor and just don't keep a reference to
        // the new class. In that case cacheLoader() tries to compile all of them, but
        // if anything goes wrong an exception will be thrown.
        //

        try {
            getCompiledRegex(regex, flags);             // ignores a returned Pattern
            compiled = true;
        } catch (PatternSyntaxException e) {
            if (silent == false) {
                System.err.println(e.getMessage());
            }
        } catch (RuntimeException e) {
            throw(e);
        }

        return(compiled);
    }


    public static boolean
    getMatched(String target, String regex)  {

        return(getMatched(target, regex, FLAGS_DEFAULT));
    }


    public static boolean
    getMatched(String target, String regex, int flags)  {

        boolean matches = false;
        Pattern pattern;

        //
        // Matches a target string against a regular expression and returns true if it
        // succeeds and false if it fails. In this method, the regex string is always
        // compiled into a Pattern class using flags as the compilation flags.
        //
        // NOTE - this is a static method, so successfully compiled regular expressions
        // are never cached. The equivalent instance method is matched().
        //

        if (target != null && regex != null) {
            if ((pattern = getCompiledRegex(regex, flags)) != null) {
                matches = getMatchedFromMatcher(pattern.matcher(target));
            }
        }

        return(matches);
    }


    public static String
    getMatchedGroup(int index, String target, String regex) {

        return(getMatchedGroup(index, target, regex, FLAGS_DEFAULT));
    }


    public static String
    getMatchedGroup(int index, String target, String regex, int flags) {

        String  group = null;
        Pattern pattern;

        //
        // Matches a target string against a regular expression and returns null if it
        // fails or there's no capture group at index, otherwise the captured group at
        // index is returned. Individual groups captured when a Java regular expression
        // is matched can be null, so a null return from this method won't always mean
        // the match failed. For example, match the regular expression
        //
        //     (aaa)|(bbb)
        //
        // against "bbb" or "ccc" using the calls
        //
        //     getMatchedGroup(1, "bbb", "(aaa)|(bbb)", FLAGS_DEFAULT)
        //
        // and
        //
        //     getMatchedGroup(1, "ccc", "(aaa)|(bbb)", FLAGS_DEFAULT)
        //
        // and both calls return null even though the match against "bbb" succeeded and
        // the match against "ccc" failed. It's really not a big deal, and in practice
        // that regular expression probably should have been written as
        //
        //     ((aaa)|(bbb))
        //
        // but it's something to be aware of when you decide to use this method (or the
        // corresponding instance method) and compare the return value to null. However,
        // if you really understand a regular expression you should be able to decide if
        // this method is appropriate. If it's not, switch to getMatchedGroups(), because
        // with that method a null return always means the match failed.
        //
        // NOTE - this is a static method, so successfully compiled regular expressions
        // are never cached. The equivalent instance method is matchedGroup().
        //

        if (target != null && regex != null) {
            if ((pattern = getCompiledRegex(regex, flags)) != null) {
                group = getGroupFromMatcher(index, pattern.matcher(target));
            }
        }

        return(group);
    }


    public static String[]
    getMatchedGroups(String target, String regex) {

        return(getMatchedGroups(target, regex, FLAGS_DEFAULT));
    }


    public static String[]
    getMatchedGroups(String target, String regex, int flags) {

        String[] groups = null;
        Pattern  pattern;

        //
        // Matches a target string against a regular expression and returns null if it
        // fails or a String[] filled with all of the captured groups if it succeeded.
        // The group at index 0 is the portion of the target string that successfully
        // matched the entire regular expression. In this method, the regex string is
        // always compiled into a Pattern class using flags as the compilation flags.
        // In addition, a null return always signals an unsuccessful match.
        //
        // This is the static method that can replicate everything that happens when a
        // bash regular expression is used. The instance version of this method, which
        // caches all compiled regular expressions, is matchedGroups().
        //
        // NOTE - individual groups in the String[] will be null if they weren't used
        // to match any part of the target string. It's not quite what happens in the
        // BASH_REMATCH array under the same circumstances.
        //

        if (target != null && regex != null) {
            if ((pattern = getCompiledRegex(regex, flags)) != null) {
                groups = getGroupsFromMatcher(pattern.matcher(target));
            }
        }

        return(groups);
    }


    public boolean
    matched(String target, String regex) {

        return(matched(target, regex, FLAGS_DEFAULT));
    }


    public boolean
    matched(String target, String regex, int flags) {

        boolean matches = false;
        Pattern pattern;

        //
        // Matches a target string against a regular expression and returns true if it
        // succeeds and false if the match fails. In this method, the regex string is
        // only compiled into a Pattern class if it's not currently cached. The flags
        // are compilation flags, but they're also included as part of the cache key.
        //
        // NOTE - this is an instance method, so it caches every successfully compiled
        // regular expression. The equivalent static method is getMatched().
        //

        if (target != null && regex != null) {
            if ((pattern = compiledRegex(regex, flags)) != null) {
                matches = getMatchedFromMatcher(pattern.matcher(target));
            }
        }

        return(matches);
    }


    public String
    matchedGroup(int index, String target, String regex) {

        return(matchedGroup(index, target, regex, FLAGS_DEFAULT));
    }


    public String
    matchedGroup(int index, String target, String regex, int flags) {

        String  group = null;
        Pattern pattern;

        //
        // Matches a target string against a regular expression and returns null if it
        // fails or there's no capture group at index, otherwise the captured group at
        // index is returned. Individual groups captured when a Java regular expression
        // is matched can be null, so a null return from this method won't always mean
        // the match failed. For example, match the regular expression
        //
        //     (aaa)|(bbb)
        //
        // against "bbb" or "ccc" using the calls
        //
        //     matchedGroup(1, "bbb", "(aaa)|(bbb)", FLAGS_DEFAULT)
        //
        // and
        //
        //     matchedGroup(1, "ccc", "(aaa)|(bbb)", FLAGS_DEFAULT)
        //
        // and both calls return null even though the match against "bbb" succeeded and
        // the match against "ccc" failed. It's really not a big deal, and in practice
        // that regular expression probably should have been written as
        //
        //     ((aaa)|(bbb))
        //
        // but it's something to be aware of when you decide to use this method (or the
        // corresponding static method) and compare the return value to null. However,
        // if you really understand a regular expression you should be able to decide if
        // this method is appropriate. If it's not, switch to matchedGroups(), because
        // with that method a null return always means the match failed.
        //
        // NOTE - this is an instance method, so it caches every successfully compiled
        // regular expression. The equivalent static method is getMatchedGroup().
        //

        if (target != null && regex != null) {
            if ((pattern = compiledRegex(regex, flags)) != null) {
                group = getGroupFromMatcher(index, pattern.matcher(target));
            }
        }

        return(group);
    }


    public String[]
    matchedGroups(String target, String regex) {

        return(matchedGroups(target, regex, FLAGS_DEFAULT));
    }


    public String[]
    matchedGroups(String target, String regex, int flags) {

        String[] groups = null;
        Pattern  pattern;

        //
        // Matches a target string against a regular expression and returns null if it
        // fails or a String[] filled with all of the captured groups if it succeeded.
        // The group at index 0 is the portion of the target string that successfully
        // matched the entire regular expression. In this method, the regex string is
        // only compiled into a Pattern class if it's not currently cached. The flags
        // are compilation flags, but they're also included as part of the cache key.
        // In addition, a null return always signals an unsuccessful match.
        //
        // This is the instance method that can replicate everything that happens when
        // a bash regular expression is used. The static version of this method, which
        // never caches compiled regular expressions, is getMatchedGroups().
        //
        // NOTE - individual groups in the String[] will be null if they weren't used
        // to match any part of the target string. It's not quite what happens in the
        // BASH_REMATCH array under the same circumstances.
        //

        if (target != null && regex != null) {
            if ((pattern = compiledRegex(regex, flags)) != null) {
                groups = getGroupsFromMatcher(pattern.matcher(target));
            }
        }

        return(groups);
    }

    ///////////////////////////////////
    //
    // Private Methods
    //
    ///////////////////////////////////

    private String
    cacheKey(String regex, int flags) {

        return((flags & FLAGS_MASK) + KEY_SEPARATOR + regex);
    }


    private int
    cacheKeyFlags(String key) {

        String[] fields;
        int      flags = FLAGS_DEFAULT;

        //
        // Extracts the compilation flags from a cache key. KEY_SEPARATOR is quoted
        // to guarantee it's treated as a literal when it's used to split the cache
        // key.
        //

        if (key != null && (fields = key.split(Pattern.quote(KEY_SEPARATOR), 2)) != null) {
            if (fields.length > 0 && fields[0].length() > 0) {
                flags = Integer.parseInt(fields[0]);
            }
        }

        return(flags & FLAGS_MASK);
    }


    private String
    cacheKeyRegex(String key) {

        String[] fields;
        String   regex = "";

        //
        // Extracts the regular expression from a cache key. KEY_SEPARATOR is quoted
        // to guarantee it's treated as a literal when it's used to split the cache
        // key.
        //

        if (key != null && (fields = key.split(Pattern.quote(KEY_SEPARATOR), 2)) != null) {
            if (fields.length > 1 && fields[1].length() > 0) {
                regex = fields[1];
            }
        }

        return(regex);
    }


    private Pattern
    compiledRegex(String regex, int flags) {

        String key;

        //
        // Look for it in the cache first. If it's not there and lockedCache is set to
        // true throw an IllegalStateException, otherwise compile and cache the regular
        // expression and then return the cached Pattern to the caller.
        //

        key = cacheKey(regex, flags);
        if (regexCache.containsKey(key) == false) {
            if (lockedCache == false) {
                regexCache.put(key, getCompiledRegex(regex, flags));
            } else {
                throw(new IllegalStateException("locked cache doesn't contain key: \"" + key + "\""));
            }
        }

        return(regexCache.get(key));
    }


    private static Pattern
    getCompiledRegex(String regex, int flags) {

        Pattern pattern = null;

        //
        // This is the only method that compiles regular expressions. Java does all the
        // hard work, and if the compilation succeeds we get an instance of the Pattern
        // class that can match strings against the compiled regular expression.
        //
        // No cache for static methods means regular expressions are compiled every time
        // this method is called. The caller, if it's an instance method, is responsible
        // for adding the returned Pattern to the cache.
        //

        if (regex != null) {
            pattern = Pattern.compile(regex, (flags & FLAGS_MASK));
        }

        return(pattern);
    }


    private static String
    getGroupFromMatcher(int index, Matcher matcher) {

        String group = null;

        //
        // Using matcher.find(0) resets the matcher, which should be unnecessary, before
        // matching the full target string against the compiled regular expression.
        //
        // NOTE - by convention, the group at index 0 is the subsequence of the original
        // target string that was matched by the entire regular expression. The capturing
        // groups defined in the regular expression start at index 1.
        //
        // NOTE - this is the low level method that returns null if the match fails, the
        // requested group doesn't exist, or the group wasn't used in a successful match.
        //

        if (matcher.find(0)) {
            if (index >= 0 && index <= matcher.groupCount()) {
                group = matcher.group(index);           // group at index could be null
            }
        }

        return(group);
    }


    private static String[]
    getGroupsFromMatcher(Matcher matcher) {

        String[] groups = null;
        int      count;
        int      index;

        //
        // Using matcher.find(0) resets the matcher, which should be unnecessary, before
        // matching the full target string against the compiled regular expression.
        //
        // NOTE - by convention, the group at index 0 is the subsequence of the original
        // target string that was matched by the entire regular expression. The capturing
        // groups defined in the regular expression start at index 1.
        //
        // NOTE - a null return from this method always means the match failed.
        //

        if (matcher.find(0)) {
            count = matcher.groupCount();
            groups = new String[count + 1];
            for (index = 0; index <= count; index++) {
                groups[index] = matcher.group(index);
            }
        }

        return(groups);
    }


    private static boolean
    getMatchedFromMatcher(Matcher matcher) {

        //
        // Using matcher.find(0), rather than matcher.matches(), resets the matcher before
        // matching the full target string against the compiled regular expression.
        //

        return(matcher.find(0));
    }
}

