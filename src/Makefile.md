## GNU Make

This is a work in progress - still lots to do...

Small shell scripts do the grunt work in makefiles, but familiarity with bash (or
any other shell) doesn't mean you'll be able to understand makefiles. Make always
preprocesses anything it hands to the shell, so you have to know some of the rules
it follows to figure out what the shell is really going to do.

This is a tiny repository that could easily be built any way you choose - even by
hand. I picked GNU make for this repository because I'm comfortable using it and
fine if it's only available on Linux systems. Make is old technology, so most of
the people writing code today probably need some help with it.

An important part of that help involved adding comments to makefiles, and that's
where I stumbled into a minor issue that I'll discuss in more detail later in this
document. It happened because I wanted to put a comment on the same line as a GNU
make variable assignment, and that eventually caused problems when the variable was
referenced later in the makefile. I was, to say the least, surprised when I figured
out that adding a comment to a makefile changed GNU make's behavior.

My intention here isn't to write a GNU make tutorial, but instead it's to give you
enough information so you'll have a shot at reading the makefiles and understanding
some of the choices made when I wrote them. Those makefiles aren't complicated, so
this shouldn't be a long document.

### The Manual

The GNU make manual

    https://www.gnu.org/software/make/manual/make.html

is the definitive reference. It's huge, and today I can't imagine anyone sitting
down and reading the whole thing, but chatbots have already done it and talking
to them is much easier than searching through the web page or using the manual's
extensive index.

Ask your favorite chatbot (or check the manual) if you run into occasional words
or phrases in this document that are unfamiliar. Just be sure the chatbot you use
knows you want information about GNU make (or gmake).

### The SHELL Variable

I don't remember when I first encountered make, but it probably happened in 1981
or 1982, so it must have been a direct descendant of AT&T's original version. At
that time GNU and POSIX didn't stand for anything and there was no doubt what you
were talking about when you mentioned the shell.

Everything was simpler back then and that's the environment I was in when I began
using make. For most of the 1980s shell code in makefiles was handed to the Bourne
shell. The situation today is different and everyone has their favorite shell. GNU
make even lets makefiles pick their preferred "shell" by pointing at it using GNU
make's special SHELL variable. For example, put

    SHELL = /bin/bash

in a makefile and all the shell code goes to /bin/bash, but if you don't set SHELL
GNU make uses /bin/sh. Unfortunately, no matter how you decide to handle SHELL in
makefiles you can't be certain what you're getting. Is /bin/bash the version that
you need (it's probably 3.2 on MacOS), does it even exist, is a better version of
bash hiding somewhere else, is GNU make's default shell (i.e., /bin/sh) really a
POSIX shell, and if so what version of POSIX does it support?

They're all legitimate questions that you probably can't answer when you're writing
a makefile. So instead of trying to point at the shell I might like to use, I don't
set SHELL in GNU makefiles (despite what the manual recommends in section 16.1) and
instead I use whatever GNU make selects. After that I just trust the advice that's
in section 16.2 of the GNU make manual

    Write the Makefile commands (and any shell scripts, such as configure) to
    run under sh (both the traditional Bourne shell and the POSIX shell), not
    csh. Don’t use any special features of ksh or bash, or POSIX features not
    widely supported in traditional Bourne sh.

and write shell code that would be accepted by a POSIX.1-1992 shell, which I think
is the standard that included the $(...) command substitution syntax.

I spent many years talking to a Bourne shell, so I find it easy to do in makefiles,
but you may not agree or even know what you can and can't say to a Bourne or POSIX
shell. In that case I expect almost any chatbot you choose could give you all the
help you need.

### Variable Names

If you poke around in the GNU make manual you'll find the following description of
variable names

    A variable name may be any sequence of characters not containing ‘:’, ‘#’,
    ‘=’, or whitespace. However, variable names containing characters other than
    letters, numbers, and underscores should be considered carefully, as in some
    shells they cannot be passed through the environment to a sub-make.

in section 6.

I was surprised - the huge character set allowed in variable names is something I
had never noticed (or maybe just never remembered). I can't think of a good reason
to use the entire character set, so I'll continue to choose makefile variable names
that a shell would accept. Leaning on the environment as the reason to "shrink the
character set" is as questionable today as it was when that sentence was added to
the manual.

### Variable Assignments

### Variable References

GNU make lets you use `$(VARNAME)` or `${VARNAME}` to reference makefile variables.
Two visually similar choices, particularly when one of them is claimed by every
shell that I'm familiar with, seems like a lousy idea.

According to ChatGPT, the `${VARNAME}` reference was added to GNU make (in about
1997) to align it with POSIX standards. Prior to that, `$(VARNAME)` was the only
way to reference makefile variables, and it's the only way I reference makefile
variables. So if you see `${VARNAME}` in any of the makefiles in this repository,
it's either a mistake or it's in a recipe (i.e., shell code), and when you "zoom
out a bit" you should see `$${VARNAME}`.

### Rules

Most of what you see in a makefile are "rules" that look like

    targets : prerequisites
            recipes

They're what make uses to decide what to do (targets), when to do it (prerequisites),
and how it's supposed to be done (recipes). The GNU make manual discusses all three
components, so that's where to go for all the details. I'm only going to talk about
recipes, because that's where you'll find the shell code that does the real work.

The recipes are where make's infamous tabs comes into play. The lines that follow
the targets and start with a tab are included in the rule's recipes, which end when
make finds a line that doesn't start with a tab. No tab indented lines means there's
nothing for make to do - it's allowed, but GNU make lets you know when that happens.

### Recipes

A recipe is a "block" of one or more tab indented lines that GNU make is supposed
to use to build the targets.

### Comments

Makefiles contain text that's either consumed by make or just preprocessed before
it's handed to the shell. Both programs (GNU make and the shell) support comments
that start with a '#' character and continue to the end of the line, but a comment
in a makefile that ends with an unescaped backslash is continued on the next line.

It's a difference between make and shell comments, but it's documented and really
isn't significant.

### Comments In Variable Definitions

More annoying is what happens when you add a comment to the end of a line, like
the definition of a makefile variable. For example, adding a short comment on the
same line as the variable definition

    KEY := VALUE                # this is used to ...

could often be helpful. Since there's no mention in the manual about what happens
here, assuming that the word VALUE is assigned to the makefile variable KEY would
be perfectly reasonable. Unfortunately, what actually happens is all of the white
space between the end of the variable assignment and the start of the comment also
ends up in the definition of KEY.

Using square brackets to mark the ends of strings, you probably should expect KEY
to be

    [VALUE]

(minus the square brackets), but instead

    [VALUE                ]

is what's actually assigned to KEY. Increase or decrease the amount of white space
between the variable assignment and the comment and the right square bracket will
move right or left. You'll need a simple makefile if you want to see for yourself,
so put the following lines

    KEY := VALUE                # this is used to ...

    print :
        @echo "[$(KEY)]"        # this line must start with a tab

in a file, say /tmp/bug.mk (making sure the echo line starts with a tab), and then
type

    make -f /tmp/bug.mk

and that should convince you ...

