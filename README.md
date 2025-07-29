# ByteDump

Right now what you'll find in this repository are the Java and bash implementations
of a program that can be used to dump the bytes in a file. My purpose here isn't to
convince anyone to use either of the programs. Instead, I wrote them to hopefully be
useful source code resources for programmers. They might be worth a look if you're a
programmer who knows bash, Java, or even GNU make.

The Java and bash versions both work on Linux, they accept the same (non-debugging)
command line options, and as far as I know they produce identical output. The bash
version was written first and it's been available on GitHub for about a year. The
Java implementation is new. It seems to work well and obviously is much faster than
the bash version, but I still have lots of work to do documenting the source code.
My guess is everything will be finished in about a month (by early September 2025),
but until then expect frequent updates (mostly to README files and the comments in
makefiles and Java class files).

# Directories

You'll find the following directories in this repository:

         src - the top level source directory
    src/bash - source code for the bash version of bytedump
    src/java - source code for the Java version of bytedump
       image - the default installation directory

# Makefiles

The three makefiles

         src/Makefile - used to manage both versions of bytedump
    src/bash/Makefile - manages the bash version of bytedump
    src/java/Makefile - manages the Java version of bytedump

are available to help you build or install the different bytedump implementations.
All three recognize a small set of targets ("all", "install", "clean", "clobber",
and "testfiles") that are documented in the comments that you'll find in each
Makefile.

# Executables

You can use any of the makefiles, but you have to be in the same directory as the
one you pick. For example, type

    cd src/java
    make all

to build the Java version of bytedump and leave all the pieces in src/java. After
that, point the executable named bytedump-java at a readable file

    ./bytedump-java /etc/hosts

and you'll get the default dump of that file. Type

    ./bytedump-java --help | less

and pretty extensive documentation will print on standard output. If you want to
build and install the Java version type

    make install

and everything needed to run it will end up somewhere under the image directory.
To install it somewhere else, like /tmp/testdir, make sure that directory exists
(the makefile won't create the top level installation directory) and then type

    make INSTALLDIR=/tmp/testdir install

The top level installation directory doesn't matter and there's no record of it
in any of the installed files, so you can move that directory anywhere you want
and all the installed bytedump executables will still work.

Do something similar in the src/bash directory, but use bytedump-bash instead of
bytedump-java, and the results (except for minor documentation differences) will
be the same. If you want to build or install everything (currently the bash and
Java versions) in one step just use the makefile in the src directory.

# Source Files

Here are a few source files that you may want to look at. I've ordered the list
so the files that I think might be most interesting and/or easiest come first.

    src/java/RegexManager.java
        Regular expression support that hides Java's Pattern and Matcher classes.

    src/java/Terminator.java
        Error support class that's used to "gracefully" stop a Java application.

    src/java/launcher_template.sh
        Bash script that "launches" a Java application.

    src/java/ByteDump.java
        The Java bytedump version - it "resembles" the bash version.

    src/bash/bytedump-bash.sh
        The bash bytedump version - it's a big file with lots of comments.

