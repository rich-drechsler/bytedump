# Bytedump Source Directory

This is the source directory where you'll find the Java and bash implementations
of an application named bytedump. The bash version has been available on GitHub
for over a year. The Java implementation is new and the program itself seems to
work well, but my goal with all of this is to end up with an approachable source
code package. If you choose to dig into the source code, whether it's bash, Java,
or GNU makefiles, I want to do what I can to help.

Two working programs that you can build, install, and run is an absolute minimum
requirement and not the final product. There's lots I still need to explain, so
expect frequent updates over the next month or two. My hope is that the missing
documentation (mostly comments in makefiles and the Java source code) can all be
finished by the end of September 2025.

# Makefiles

More...

# Bash Version

More...

# Java Version

I think what's here works and I'm reasonably satisfied with the new Java version,
but you'll undoubtedly have to work harder than I originally hoped to follow the
source code and understand some the decisions I made in the Java implementation.
Besides requiring that the bash and Java versions accept the same (non-debugging)
options and produce identical output, I also imposed the vague constraint,

    The Java and bash versions should "resemble" each other closely enough
    that understanding one of the implementations could help you understand
    the other.

on the source code in the Java and bash implementations. If you're curious about
what "resemble" means take a look at the

    bash/bytedump-bash.sh

and

    java/ByteDumpBash.java

files - even though they're completely different languages I think you'll be able
see some similarity.

# Coming Someday (maybe)...

Implementations in languages, like Python, Rust, or C, but the bash constraint
that I imposed on the existing Java version will undoubtedly be dropped. Right
now my only plans are to finish the Java and makefile documentation. After that
I may try another language.

# Chatbot Inquisitions

One thing I originally wanted to do was see how well chatbots handled the job of
"translating" the bash version into Java. I wasn't at all interested in watching
them generate Java code, but instead I just wanted to see if they could describe
the steps they would follow to accomplish the task. They would have to understand
the bash version and the constraints on the translation, and that would all be my
responsibility. If I was convinced a chatbot understood the bash version and the
goal, the chat could focus on finding out how that chatbot might tackle the job.

My Java implementation is one answer, but I wanted to make sure chatbots came up
with their own solutions, so delaying the public release of the Java version made
sense to me. Nobody else would waste time translating the bash implementation of
bytedump into Java. In fact, I'd be very surprised if any chatbot has encountered
a non-trivial bash script that was intentionally translated into an "equivalent"
Java program.

I eventually ran a few simple chatbot experiments and even though they didn't go
very far, afterwards I lost some of my initial interest. At this point I'm just
not sure I'll go back to it - a publicly available "solution" to the question I
wanted to ask chatbots would make it really hard for me to identify success.

