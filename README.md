## ByteDump

Right now, what you'll in this repository are Java, bash, and Python implementations
of a program that can be used to dump the bytes in a file. My purpose here isn't to
convince anyone to use the existing programs. Instead, I wrote them to hopefully be
useful source code resources for programmers. They accept the same (non-debugging)
command line options, generate identical output, and if you look at the source code
I'm pretty sure you'll notice quite a bit of similarity across the three versions.
They're extensively commented and might be worth a look if you're familiar with (or
perhaps just curious about) Java, bash, Python, or even GNU make.

The development and testing was done on Linux. The bash version was written first,
uploaded to GitHub as a standalone application in 2024, and was moved into to this
repository on July 29 2025, along with the new Java implementation of bytedump. The
initial Python program was created by Gemini 3.0 Pro (with a little coaching from
me) and that version was added to this repository on Dec 23 2025. Since then every
commit on my Linux system was pushed to this repository, primarily because I wanted
to make sure everyone could track the gradual evolution of Gemini's original Python
program into the version that's currently available.

There's some code cleanup left and a bunch of missing or incomplete documentation
that really needs to be addressed. I'll probably work on all of it slowly over the
next month or two, and after that work is finished I'll decide about implementing
bytedump in another programming language. There have been lots of clones of this
repository, but I have no idea how to translate GitHub clone counts into interest,
so consider visiting

    https://github.com/rich-drechsler/bytedump/issues/2

and leaving a reaction and/or comment if you want me to tackle another language.

### Directories

You'll find the following directories in this repository:

           src - the top level source directory
      src/bash - source code for the bash version of bytedump
      src/java - source code for the Java version of bytedump
    src/python - source code for the Python version of bytedump
         image - the default installation directory

Implementations in any additional languages will be stored in directories that, just
like the bash, Java, and Python versions, identify the language.

### Makefiles

The makefiles

      src/bash/Makefile - manages the bash version of bytedump
      src/java/Makefile - manages the Java version of bytedump
    src/python/Makefile - manages the Python version of bytedump
           src/Makefile - manages all of the bytedump implementations

are available to help you build or install the different bytedump implementations.
Each one recognizes a small set of targets (`all`, `install`, `clean`, `clobber`,
`testfiles`, and `validate`) that are documented in comments that you'll find in
each makefile. Those targets can be supplied as command line arguments when you
run make, but if you just type

    make

every makefile in this repository assumes you meant

    make all

That's often what happens in makefiles, but the choice of the "default target" is
always completely controlled by GNU makefiles.

### Executables

You can use any of the makefiles, but you have to be in the same directory as the
one you plan on using. For example (assuming you're in the same directory as this
file) you can type

    cd src/java
    make

to build the Java version of bytedump and leave all the pieces in `src/java`. After
that, point the executable named `bytedump-java` at any readable file

    ./bytedump-java /etc/hosts

and you'll get the default dump of that file. If you want documentation type

    ./bytedump-java --help | less

and a pretty complete description of the bytedump program and the supported command
line options will print on standard output. That same --help option works in all of
the bytedump implementations.

### Installation

Being able to build and run different language dependent bytedump implementations
from their source directories is convenient if you're a programmer, but being able
to copy all of the pieces needed to run them into another directory is also useful.
It's a job that every makefile in this repository handles when you tell it to build
the `install` target. For example, type

    cd src/java
    make install

and everything needed to run the Java version of bytedump will be built and copied
into the directory named `image` that's located in the same directory as this file.
To install it somewhere else, like `/tmp/bytedump`, make sure the directory exists
(the makefile won't create the top level installation directory) and then type

    make INSTALLDIR=/tmp/bytedump install

The name of the top level installation directory doesn't matter. There's no record
of it in any of the installed files, so you can move that directory anywhere you
want and all the installed bytedump executables will continue to work.

### Source Files

Here are a few source files that you may want to look at. I've ordered the list so
the files that I think might be most interesting and/or easiest come first.

    src/java/RegexManager.java
        Regular expression support that hides Java's Pattern and Matcher classes.

    src/java/Terminator.java
        Error support class that's used to "gracefully" stop a Java application.

    src/java/launcher_template.sh
        Bash script that "launches" a Java application - I believe it's a decent
        example of what bash really should be used for.

    src/java/ByteDump.java
        The Java bytedump version - it "resembles" the bash version.

    src/python/bytedump-python.py
        The Python bytedump version - modified from Gemini's original program

    src/bash/bytedump-bash.sh
        The bash bytedump version - it's a big file with lots of comments.

The bash version is, without a doubt, the toughest read and it was easily the most
challenging to write. More than half the lines in the script are comments that I hope
help anyone who decides to take a closer look at the source code. Many of the comments
try to explain what I was thinking when I wrote portions of the bash script, so if you
don't agree with my thoughts you won't have to waste time deciphering chunks of bash
code just to decide the author really was crazy. There really are enough comments,
particularly at the start of `bytedump-bash.sh`, that you probably can make that
decision without looking at any bash code.

