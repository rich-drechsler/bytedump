## ByteDump

Right now, what you'll find in this repository are the Java and bash implementations
of a program that can be used to dump the bytes in a file. My purpose here isn't to
convince anyone to use either of the programs. Instead, I wrote them to hopefully be
useful source code resources for programmers - they might be worth a look if you're
familiar with (or perhaps just curious about) Java, bash, or even GNU make.

The Java and bash versions both work on Linux. They accept the same (non-debugging)
command line options and as far as I know also produce identical output. The bash
version was written first and uploaded to a public GitHub repository in 2024. The
Java implementation is new, but seems to work well and is almost always much faster
than the bash script. Both versions are available in this repository and if I get
time I plan on adding implementations in a few more languages (e.g., Python, Rust,
or C).

### Chatbots

Gemini 3 Pro did a pretty good job translating the Java version into Python, and I
was pleased with the results. It's not complete or thoroughly tested, but it does
seem to work, so I decided to include it this repository. Gemini 3 Pro handled all
of the translation with only a little interference from me. No makefile or anything
else yet, but I still think what's there is worth a look. I'll probably spend a week
or so working on it, and perhaps after that I'll get back to the documentation that
I've been postponing for the last few months.

### Directories

You'll find the following directories in this repository:

           src - the top level source directory
      src/bash - source code for the bash version of bytedump
      src/java - source code for the Java version of bytedump
    src/python - preliminary source code for the Python version of bytedump
         image - the default installation directory

Implementations in any additional languages will be stored in directories that, just
like the bash, Java, and Python versions, identify the language.

### Makefiles

The makefiles

      src/bash/Makefile - manages the bash version of bytedump
      src/java/Makefile - manages the Java version of bytedump
    src/python/Makefile - manages the Java version of bytedump
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
always completely controlled by each makefile.

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
line options will print on standard output.

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

The initial Python version was built

