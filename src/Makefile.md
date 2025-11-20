# GNU Make

Small shell scripts do the grunt work in makefiles, but familiarity with bash (or
any other shell) doesn't mean you'll be able to understand makefiles. Make always
preprocesses anything it hands to the shell, so you have to know some of the rules
it follows to figure out what the shell is really going to do. My plan here is to
briefly discuss GNU make, but limit what's covered to things I believe will help
you follow the makefiles in this repository. Those makefiles aren't complicated,
so this should not be a long document.

This is a tiny repository that could easily be built any way you choose - even by
hand. I picked GNU make because I'm comfortable using it and primarily interested
in building the different programs on Linux systems. Make is old technology, and
I suspect most active programmers will want some help with it. An important part
of that help involved adding comments to the makefiles, but placing some of those
comments exactly where I wanted sometimes triggered strange behavior when GNU make
used the makefiles. They were subtle problems that I just didn't notice for quite
a while - I'll provide more details when I discuss makefile comments later in this
document.

## The Manual

The GNU make manual, which can be found at the URL

    https://www.gnu.org/software/make/manual/make.html

is the definitive reference. It's huge, and today I can't imagine anyone sitting
down and reading the whole thing - that's something chatbots have already done and
talking to them is much easier than searching through the manual. But the manual
is still useful, so I'll occasionally reference section numbers and include short
quotes from the version that was available on 11/10/25.

## The SHELL Variable

I don't remember when I first encountered make, but it probably happened in 1981,
and the version that I used was definitely a direct descendant of AT&T's original
implementation. At that time GNU and POSIX didn't stand for anything and there was
no doubt what you were talking about when you mentioned the shell.

Everything was simpler back then and that's the environment I was in when I began
struggling with make. For much of the 1980s shell code in makefiles was handed to
the Bourne shell. The situation today is different and everyone has their favorite
shell. GNU make even lets makefiles pick their preferred "shell" by pointing at it
using GNU make's special SHELL variable. For example, put

    SHELL = /bin/bash

in a makefile and all the shell code goes to /bin/bash, but if you don't set SHELL
GNU make uses /bin/sh. Unfortunately, no matter how you decide to handle SHELL in
makefiles you can't be certain what you're getting. Is /bin/bash the version that
you expect (on macOS it's likely 3.2), does it even exist, is a better version of
bash hiding somewhere else, is GNU make's default shell (i.e., /bin/sh) really a
POSIX shell, and if so, what version of POSIX does it support?

They're all legitimate questions that you usually can't answer when you're writing
a makefile. So instead of trying to point at my favorite shell, I never set SHELL
in GNU makefiles (despite what the manual recommends in section 16.1) and instead
I let GNU make choose the shell. After that, I follow the advice in Section 16.2
of the GNU make manual

  > Write the Makefile commands (and any shell scripts, such as configure) to
  > run under sh (both the traditional Bourne shell and the POSIX shell), not
  > csh. Don’t use any special features of ksh or bash, or POSIX features not
  > widely supported in traditional Bourne sh.

and try to write shell code that would be accepted by a POSIX.2-1992 shell, which
I believe is the standard that included the $(...) command substitution syntax. If
GNU make exists on a system then makefiles should be able to safely assume that a
POSIX shell also exists on that system.

I spent many years talking to a Bourne shell, so I find it easy to do in makefiles,
but you may not agree or even know what you can and can't say to a Bourne or POSIX
shell. In that case I expect almost any chatbot you choose could give you all the
help you need.

## Variable Names

If you poke around in the GNU make manual you'll find the following description of
variable names

  > A variable name may be any sequence of characters not containing ‘:’, ‘#’,
  > ‘=’, or whitespace. However, variable names containing characters other than
  > letters, numbers, and underscores should be considered carefully, as in some
  > shells they cannot be passed through the environment to a sub-make.

in the introduction to section 6.

As far as I can tell (by asking three different chatbots) this really is GNU make's
official variable name character set. It's much bigger than the character set used
in AT&T's original version of make or by any serious programming language that I've
ever encountered. Makefiles in this repository don't need this expanded character
set, so all variable names consist entirely of letters, numbers, and underscores.

GNU make also supports built-in functions (about 25 of them) that all have lowercase
names and are called using a syntax that could be mistaken for a variable reference.
So to avoid confusion and possible collisions with built-in functions, variable names
in these makefiles also never use lowercase letters.

## Setting Variables

After you've picked a name for a makefile variable you'll want to assign a value to
it. GNU make supports a pretty confusing collection of assignment operators that are
listed together in the first paragraph in section 6.5 of the GNU manual

  > To set a variable from the makefile, write a line starting with the variable
  > name followed by one of the assignment operators ‘=’, ‘:=’, ‘::=’, or ‘:::=’.
  > Whatever follows the operator and any initial whitespace on the line becomes
  > the value.

In fact that's not the complete list - just read a few more paragraphs in the manual
and you'll encounter discussions of the `?=`, `!=` and `+=` assignment operators.

Adjectives, like "recursively", "simply", or "immediately", that the manual uses to
talk about various assignment operators never really helped me connect them to actual
situations where each one might be needed. Fortunately, the only assignment operator
used by the makefiles in this repository is `:=`, and if you just pretend it works
something like the shell's assignment operator (without any quoting) you'll probably
be fine.

## Using Variables

GNU make lets you use `$(VARNAME)` or `${VARNAME}` to reference makefile variables,
but two visually similar choices, particularly when `${VARNAME}` was claimed by the
original Bourne shell (in 1979), seems like a bad idea.

According to ChatGPT, the `${VARNAME}` syntax was added to GNU make (in about 1997)
to align it with POSIX standards for `make`. Before that, `$(VARNAME)` was the only
way to reference makefile variables, and it's the only syntax that the makefiles in
this repository use to access the value stored in a makefile variable.

So, if you see `${VARNAME}` in any of these makefiles it's either a careless mistake
(on my part) or it's in a recipe (i.e., shell code) and when you "zoom out a bit" you
should see `$${VARNAME}`. The two dollar signs are the escape sequence that you must
use in makefile recipes whenever you want to pass a single dollar sign to the shell.

## Rules

Most of what you see in a makefile are "rules" that look like

    targets : prerequisites
            recipes

They're what make uses to decide what to do (targets), when to do it (prerequisites),
and how it's supposed to be done (recipes). The GNU make manual discusses all three
components, so that's where to go for all the details. I'm only going to talk about
recipes in this document, because that's where you'll find the shell code that does
the real work.

## Recipes

Recipes are where make's infamous tabs come into play. Lines that follow the targets
and start with a tab are included in the rule's recipes, which end when make finds a
line that doesn't start with a tab. No tab indented lines means there's nothing for
make to do - it's allowed, but GNU make lets you know when that happens.

## Comments

Makefiles contain text that's either consumed by make or just preprocessed before
it's handed to the shell. Both programs (GNU make and the shell) support comments
that start with a '#' character and continue to the end of the line, but a comment
in a makefile that ends with an unescaped backslash is continued on the next line.

It's a difference between make and shell comments that's documented in the manual,
but isn't something that's used in any of the makefiles in this repository.

## Comments In Variable Definitions

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

is what's actually assigned to KEY. Increase or decrease the amount of whitespace
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

