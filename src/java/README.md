# Bytedump - Java Version

The Java version works and I'm satisfied with it, but I'm not at all happy with
the state of the documentation (mostly comments in Java files and the makefile).
My guess is I'll be able to finish all of the documentation by early September.
Until then, expect frequent updates.

# Interesting Files

The most interesting source code files probably are

    ByteDump.java
    RegexManager.java
    Terminator.java
    StringTo.java
    launcher_template.sh

If you want to compare the Java and bash implementations, take a close look at

    ByteDump.java
    Terminator.java

and I think you'll see some similarity to the bash version

    ../bash/bytedump-bash.sh

The bash script named launcher_template.sh is also interesting, but you probably
need to look at the Makefile to see how it's used to build the

    bytedump-java

bash script that launches the Java version of bytedump.

# Building The Java Version

Type

    make

or equivalently

    make all

and you'll end up with a bash script named bytedump-java that you use to run the
Java version. Type

    ./bytedump-java --help

or

    ./bytedump-java --help | less

to see the help documentation (or just read the ByteDump.help file). The Java and
bash versions recognize the same (non-debugging) options and as far as I can tell
they produce identical dumps.

