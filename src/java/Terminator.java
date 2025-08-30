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

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;

/*
 * This class represents an error handling framework that Java applications can use
 * to generate consistent one-line messages for users and then, if appropriate, shut
 * the application down gracefully by throwing a custom RuntimeException (or Error)
 * instead of using System.exit().
 *
 * NOTE - in Java source files I only use block style comments, like the one you're
 * reading right now, outside class definitions, because that means they're usually
 * available for temporarily commenting out one or more lines of Java code.
 */

public
class Terminator {

    //
    // These are constants used in messageFormatter() to select some of the information
    // that's included in the final message that's returned to the caller. They get to
    // messageFormatter() (usually through the call made by errorHandler()) as a comma
    // separated, case independent list built from strings assigned to these constants.
    // That list is handed to messageFormatter() as the argument of its -info option.
    //

    public static final String CALLER_INFO = "CALLER";
    public static final String LINE_INFO = "LINE";
    public static final String LOCATION_INFO = "LOCATION";
    public static final String METHOD_INFO = "METHOD";
    public static final String SOURCE_INFO = "SOURCE";

    //
    // A few strings that messageFormatter() uses to remember information that's been
    // extracted from the StackTraceElement that describes the selected "stack frame".
    // Values assigned to these constants aren't tied to the previous group - the only
    // requirement is that they're three completely different strings.
    //

    private static final String FRAME_LINE = "LINE";
    private static final String FRAME_METHOD = "METHOD";
    private static final String FRAME_SOURCE = "SOURCE";

    //
    // These constants are only used to build the error message if, for whatever reason,
    // there's no source file or line number information in the StackTraceElement that's
    // used by messageFormatter() to build the final message.
    //
    // NOTE - messageFormatter() always adds "Line", as a prefix, to line numbers that
    // are included in the final message, so the prefix is omitted in UNKNOWN_LINE_TAG.
    //

    private static final String UNKNOWN_FILE_TAG = "File unknown";
    private static final String UNKNOWN_LINE_TAG = "unknown";

    //
    // A subclass of RuntimeException or Error is thrown by errorHandler() when it wants
    // the program to exit. Those extensions are static nested classes that are declared
    // later in this class. The boolean assigned to RUNTIME_EXCEPTION is what's used (by
    // the terminate() method) to pick the nested class that's thrown to force an exit.
    //
    // NOTE - the only excuse for using the Error extension would be if RuntimeExceptions
    // were caught somewhere that interfered with its propagation all the way back to the
    // application's main() method.
    //

    private static final boolean RUNTIME_EXCEPTION = true;

    //
    // The default status that terminate stores in the ExitException (or ExitError) that
    // it throws. That status, whatever it is, can be used or ignored when the Exception
    // or Error is caught, so it's really just a suggestion.
    //

    private static final int DEFAULT_EXIT_STATUS = 1;

    ///////////////////////////////////
    //
    // Terminator Methods
    //
    ///////////////////////////////////

    public static String
    errorHandler(String... args) {

        ArrayList<String> arguments;
        RegexManager      manager;
        String[]          groups;
        boolean           done;
        boolean           exit;
        boolean           runtime;
        String            arg;
        String            message;
        String            optarg;
        String            opttag;
        String            target;
        int               status;
        int               index;

        //
        // A method that builds an error message from its arguments. That message is either
        // returned to the caller or included as the message in a RuntimeException or Error
        // subclass that's created and thrown when the caller wants to force the program to
        // stop. The main() method in ByteDump.java is the place to look if you want to see
        // how the exception (or error) can be handled.
        //
        // The +exit-error and +exit-exception options make sure the caller gets to decide
        // whether an extension of Java's RuntimeException or Error class is thrown to stop
        // the program. The +exit option throws the default unchecked exception, which is
        // selected using the boolean value assigned to RUNTIME_EXCEPTION.
        //
        // NOTE - options supported by this method make it a particularly useful way define
        // error handling convenience methods. Take a look at the definitions of methods,
        // like internalError() or userError(), in ByteDump.java for simple examples.
        //
        // NOTE - this method intentionally doesn't use System.exit() to stop the program.
        // System.exit() is a brute force, hard stop approach that just doesn't belong in
        // a class that might be used by different applications.
        //

        exit = true;
        runtime = RUNTIME_EXCEPTION;
        status = DEFAULT_EXIT_STATUS;

        arguments = new ArrayList<>();
        arguments.add("-tag=Error");
        arguments.add("-info=location");

        manager = new RegexManager();           // for parsing the arguments
        done = false;                           // for early loop exit

        for (index = 0; index < args.length; index++) {
            arg = args[index];
            if ((groups = manager.matchedGroups(arg, "^(([+-])[^=+-][^=]*)(([=])(.*))?$")) != null) {
                target = groups[1];
                opttag = groups[2];
                optarg = groups[5];
            } else {
                target = arg;
                opttag = "";
                optarg = "";
            }

            switch (target) {
                case "+exit":
                    exit = true;
                    runtime = RUNTIME_EXCEPTION;
                    break;

                case "-exit":
                    exit = false;
                    break;

                case "+exit-error":
                    exit = true;
                    runtime = false;
                    break;

                case "+exit-exception":
                    exit = true;
                    runtime = true;
                    break;

                case "-status":
                    try {
                        status = Integer.parseInt(optarg);
                    } catch (NumberFormatException e) {}
                    break;

                case "--":
                    done = true;
                    index++;
                    break;

                default:
                    switch (opttag) {
                        case "+":
                        case "-":
                            arguments.add(arg);
                            break;

                        default:
                            done = true;
                            break;
                    }
                    break;
            }

            if (done) {
                break;          // leave the loop before index changes
            }
        }

        //
        // Add a few control options and anything left in args[] to the arguments List,
        // then hand everything in arguments to messageFormatter(), which is where the
        // final message is built.
        //

        arguments.add("+frame");
        arguments.add("--");
        arguments.add(String.join(" ", Arrays.copyOfRange(args, index, args.length)));

        message = messageFormatter(arguments.toArray(new String[0]));

        if (exit == true) {
            terminate(message, null, status, runtime);
        }

        return(message);                // or return the message to the caller
    }

    //
    // These terminate() methods all end up throwing the exception (or error) that's
    // supposed to stop the application. The main() method in ByteDump.java catches
    // the exception and is the place to look if you want an example.
    //

    public static void
    terminate() {

        terminate(null, null, 0, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(int status) {

        terminate(null, null, status, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(String message) {

        terminate(message, null, DEFAULT_EXIT_STATUS, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(String message, int status) {

        terminate(message, null, status, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(Throwable cause) {

        terminate(null, cause, DEFAULT_EXIT_STATUS, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(String message, Throwable cause) {

        terminate(message, cause, DEFAULT_EXIT_STATUS, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(String message, Throwable cause, int status) {

        terminate(message, cause, status, RUNTIME_EXCEPTION);
    }


    public static void
    terminate(String message, Throwable cause, int status, boolean runtime) {

        if (runtime) {
           throw(new Terminator.ExitException(message, cause, status));
        } else {
           throw(new Terminator.ExitError(message, cause, status));
        }
    }

    ///////////////////////////////////
    //
    // Private Methods
    //
    ///////////////////////////////////

    private static String
    messageFormatter(String args[]) {

        HashMap<String, String> caller;
        StackTraceElement[]     stack;
        RegexManager            manager;
        String[]                groups;
        boolean                 done;
        String                  arg;
        String                  message;
        String                  optarg;
        String                  opttag;
        String                  target;
        String                  info;
        String                  prefix;
        String                  suffix;
        String                  tag;
        int                     frame;
        int                     index;

        //
        // Builds a string that usually ends up as a one line message that's included in
        // the information displayed to a user when something goes wrong. The strings in
        // args[] are interpreted as options that give the caller some control over what
        // happens here or as individual strings that are joined together (using a space
        // as the separator) and included in the final message.
        //
        // NOTE - this method is only used by errorHandler() and I'm not convinced it has
        // much value anywhere else, so it's currently private.
        //

        message = null;
        info = null;
        prefix = null;
        suffix = null;
        tag = null;
        frame = 1;

        manager = new RegexManager();           // for parsing the arguments
        done = false;                           // for early loop exit

        for (index = 0; index < args.length; index++) {
            arg = args[index];
            if ((groups = manager.matchedGroups(arg, "^(([+-])[^=+-][^=]*)(([=])(.*))?$")) != null) {
                target = groups[1];
                opttag = groups[2];
                optarg = groups[5];
            } else {
                target = arg;
                opttag = "";
                optarg = "";
            }

            switch (target) {
                case "+frame":
                    frame += 1;
                    break;

                case "-frame":
                    frame = 0;
                    break;

                case "-info":
                    info = optarg;
                    break;

                case "-prefix":
                    prefix = optarg;
                    break;

                case "-suffix":
                    suffix = optarg;
                    break;

                case "-tag":
                    tag = optarg;
                    break;

                case "--":
                    done = true;
                    index++;
                    break;

                default:
                    switch (opttag) {
                        case "+":
                        case "-":
                            break;

                        default:
                            done = true;
                            break;
                    }
                    break;
            }

            if (done) {
                break;          // leave the loop before index changes
            }
        }

        if (index < args.length) {
            message = String.join(" ", Arrays.copyOfRange(args, index, args.length));
        }

        if (info != null) {
            stack = (new Throwable()).getStackTrace();
            if (frame < stack.length) {
                caller = new HashMap<>();
                caller.put(FRAME_LINE, (stack[frame].getLineNumber() >= 0) ? String.valueOf(stack[frame].getLineNumber()) : UNKNOWN_LINE_TAG);
                caller.put(FRAME_METHOD, stack[frame].getMethodName());
                caller.put(FRAME_SOURCE, (stack[frame].getFileName() != null) ? stack[frame].getFileName() : UNKNOWN_FILE_TAG);

                for (String token : info.split(",")) {
                    switch (token.trim().toUpperCase()) {
                        case CALLER_INFO:
                            tag = String.join(
                                "",
                                tag,
                                "] [",
                                caller.get(FRAME_SOURCE) + "; " + caller.get(FRAME_METHOD) + "; " + "Line " + caller.get(FRAME_LINE)
                            );
                            break;

                        case LINE_INFO:
                            tag = String.join("", tag, "] [", "Line " + caller.get(FRAME_LINE));
                            break;

                        case LOCATION_INFO:
                            tag = String.join(
                                "",
                                tag,
                                "] [",
                                caller.get(FRAME_SOURCE) + "; " + "Line " + caller.get(FRAME_LINE)
                            );
                            break;

                        case METHOD_INFO:
                            tag = String.join("", tag, "] [", caller.get(FRAME_METHOD));
                            break;

                        case SOURCE_INFO:
                            tag = String.join("", tag, "] [", caller.get(FRAME_SOURCE));
                            break;
                    }
                }
            }
        }

        return(
            String.join(
                "",
                (prefix != null && prefix.length() > 0) ? (prefix + ": ") : "",
                (message != null && message.length() > 0) ? (message + " ") : "",
                (tag != null && tag.length() > 0) ? "[" + tag + "]" : "",
                (suffix != null && suffix.length() > 0) ? suffix : ""
            )
        );
    }

    ///////////////////////////////////
    //
    // Terminator.ExitException
    //
    ///////////////////////////////////

    public static
    class ExitException extends java.lang.RuntimeException {

        //
        // An instance of this class is thrown by terminate() when it's called to stop
        // the program using an extension of Java's RuntimeException class. It's a public
        // static class that you reference in a catch block as Terminator.ExitException.
        //

        private int status = DEFAULT_EXIT_STATUS;

        //
        // Make javac happy
        //

        private static final long serialVersionUID = 1L;

        public
        ExitException() {

            this(null, null, DEFAULT_EXIT_STATUS);
        }


        public
        ExitException(String message) {

            this(message, null, DEFAULT_EXIT_STATUS);
        }


        public
        ExitException(String message, int status) {

            this(message, null, status);
        }


        public
        ExitException(String message, Throwable cause, int status) {

            super(message, cause);
            this.status = status;
        }


        public int
        getStatus() {

            return(status);
        }
    }

    ///////////////////////////////////
    //
    // Terminator.ExitError
    //
    ///////////////////////////////////

    public static
    class ExitError extends java.lang.Error {

        //
        // An instance of this class is thrown by terminate() when it's called to stop the
        // program using an extension of Java's Error class. This is a public static class
        // that you reference in a catch block as Terminator.ExitError.
        //
        // NOTE - this isn't the preferred way to stop an application, but could be useful
        // when Terminator.ExitException, which extends RuntimeException, isn't guaranteed
        // to make it all the way back to the application's main() method.
        //

        private int status = DEFAULT_EXIT_STATUS;

        //
        // Make javac happy
        //

        private static final long serialVersionUID = 1L;

        public
        ExitError() {

            this(null, null, DEFAULT_EXIT_STATUS);
        }


        public
        ExitError(String message) {

            this(message, null, DEFAULT_EXIT_STATUS);
        }


        public
        ExitError(String message, int status) {

            this(message, null, status);
        }


        public
        ExitError(String message, Throwable cause, int status) {

            super(message, cause);
            this.status = status;
        }


        public int
        getStatus() {

            return(status);
        }
    }
}

