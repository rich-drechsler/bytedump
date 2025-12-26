## GNU Make

This is a tiny repository that could easily be built any way you choose - even by
hand. I picked GNU make because I'm comfortable using it and primarily interested
in building the different programs on Linux systems. Make is old technology, and
I suspect most active programmers will want some help with it.

Small shell scripts do the grunt work in makefiles, but familiarity with bash (or
any other shell) doesn't mean you'll be able to understand makefiles. Make always
preprocesses anything it hands to the shell, so you have to know some of the rules
it follows to figure out what the shell is really going to do. My plan here is to
briefly discuss GNU make, but limit what's covered to things I believe will help
you follow the makefiles in this repository. Those makefiles aren't complicated,
so this should not be a long document.

Part of the help also involved adding comments to the makefiles, but placing those
comments exactly where I wanted sometimes triggered strange behavior that could be
traced back to how GNU make parsed those lines in the makefiles. They were subtle
issues that I didn't notice for quite a while, but when I did I was suprised (and
little embarassed) because I've been using make for a very long time. As far as I
can tell it's not behavior that originated with GNU make. I decided to include a
brief discussion of the issues in the [Comment Problems](#comment-problems) section
that I hope explains why some pretty obvious explanations don't appear as makefile
comments where they might be most helpful.

### The Manual

The GNU make manual, which can be found at the URL

    https://www.gnu.org/software/make/manual/make.html

is the definitive reference. It's huge, and today I can't imagine anyone sitting
down and reading the whole thing - that's something chatbots have already done and
talking to them is much easier than searching through the manual. But the manual
is still useful, so I'll occasionally reference section numbers and include short
quotes from the version that was available on 11/10/25.

### The SHELL Variable

I don't remember when I first encountered make, but it probably happened in 1981,
and the version I used was a direct descendant of AT&T's original implementation.
At that time GNU and POSIX didn't stand for anything and there was no doubt what
people were talking about when they mentioned the shell.

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
bash hiding somewhere else, is GNU make's default shell (i.e., whatever happens to
be installed as /bin/sh) really a POSIX shell, and if so what version of POSIX does
it support?

They're all legitimate questions that you usually can't answer when you're writing
a makefile. So instead of trying to point at my favorite shell, I never set SHELL
in GNU makefiles (despite what the manual recommends in section 16.1) and instead
I let GNU make pick the shell. After that, I follow the advice in Section 16.2 of
the GNU make manual

  > Write the Makefile commands (and any shell scripts, such as configure) to
  > run under sh (both the traditional Bourne shell and the POSIX shell), not
  > csh. Don’t use any special features of ksh or bash, or POSIX features not
  > widely supported in traditional Bourne sh.

and try to write shell code that would be accepted by a POSIX.2-1992 shell, which
I believe is the standard that included the $(...) command substitution syntax. If
GNU make exists on a system then makefiles should be able to safely assume that a
POSIX shell exists somewhere on that system.

I spent many years talking to a Bourne shell, so I find it easy to do in makefiles,
but you may not agree or even know what you can and can't say to a Bourne or POSIX
shell. If that's the case, almost any chatbot you choose probably can give you all
the help you need.

### Variable Names

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
ever encountered. Makefiles in this repository don't need this huge character set,
so variable names consist entirely of letters, digits, and underscores.

GNU make also supports built-in functions (about 25 of them) that all have lowercase
names and are called using a syntax that could be mistaken for a variable reference.
To avoid that confusion and potential collisions with built-in function names, all
variables defined in these makefiles avoid lowercase letters in their names.

### Setting Variables

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

### Using Variables

GNU make lets you use `$(VARNAME)` or `${VARNAME}` to reference makefile variables,
but two visually similar choices, particularly when `${VARNAME}` was claimed by the
original Bourne shell (in 1979), seems like a bad idea.

According to ChatGPT, the `${VARNAME}` syntax was added to GNU make (in about 1997)
to align it with POSIX standards for `make`. Before that, `$(VARNAME)` was the only
way to reference makefile variables, and it's the only syntax that the makefiles in
this repository use to access the value stored in a makefile variable.

So, if you see `${VARNAME}` in any of these makefiles it's either a careless mistake
(on my part) or it's in a recipe (i.e., code that's eventually and handed to a shell)
and when you "zoom out a bit" you should see `$${VARNAME}`. The two dollar signs are
the escape sequence that you have to use in makefile recipes when you want to pass a
single dollar sign to the shell.

### Rules

The "rules" that you'll find in the makefiles in this repository look something like

    targets : prerequisites
            recipe

They're what make uses to decide what to do (targets), when to do it (prerequisites),
and how it's supposed to be done (recipe). Prerequisites and the recipe can be empty,
but targets can't be. If a rule doesn't have any prerequisites make always runs its
recipe; if a rule doesn't have a recipe make lets you there's nothing to do - before
it actually does nothing. Eliminating that complaint is why rules in these makefiles
that don't do any real work always contain a one shell line comment that explains why
the comment is there.

The GNU make manual discusses all three components in great detail. Identifying and
understanding a rule's targets and prerequisites isn't particularly difficult, so my
plan is to ignore them and instead focus on how to decipher the makefile recipes that
you'll find in this repository. Recipes end up as shell code that does the real work,
so if you can read them you have a decent chance of understanding what a makefile is
trying to do.

### Recipes

The makefile that you'll find in the same directory as this document is really just
a small shell script that's masquerading as a makefile, and there's nothing it does
that couldn't be easily handled by a standalone shell script. Despite that, I think
it's an excellent reference for this section's topic and it's the makefile I'll use
when I want to point you at recipe code that's available (so you can fiddle around
with it) and really does work.

There's only one rule in that makefile and I recommend you take a look at it as you
read this section. Find that rule (it's simple) and make sure you recognize that it
has 6 targets, no prerequisites, and about 60 lines of indented text that look like
they "belong" to the rule. If forced, I'm sure you would guess that those 60 lines
are the rule's "recipes", but to be sure you need to verify that each indented line
starts with a tab character. It's a check you can do in an editor like vim (as long
as it's not automatically converting tabs into spaces) or by typing something like

    cat -T Makefile | less

and then looking for the character sequence ^I at the start of each indented line.

#### Partitioning Recipes

Once you know which lines belong to a recipe, you can separate them into disjoint
groups, exactly the way GNU make does. You start at the first line, add it to the
current group, and check if it ends with a backslash. If it does the next line is
added to the current group and checked for a trailing backslash. The process used
to build the group continues until make encounters a line that doesn't end with a
bashslash. If there's anything left in the recipe, make starts a new group that's
constructed just like previous groups, and make continues the process until there
are no more lines are left in the rule's recipe.

This partitioning into disjoint groups makes no changes to the recipe, but instead
just organizes it into lines that are preprocessed together by GNU make and then
handed to a new instance of the shell. I'll discuss preprocessing in the next few
sections, but at this point I think it might be worthwhile if you tried to mentally
partition the recipe in this directory's makefile. Don't try to understand what the
lines are doing - just look at the last character on each line and count the number
of groups.


This partitioning into disjoint groups makes no changes to the recipe, but instead
just organizes it into lines that are preprocessed together by GNU make and then
handed to a new instance of the shell. I'll discuss preprocessing in the next few
sections, but at this point I think it would be useful for you to take a look at
the recipe in the makefile 

#### Reading Recipes

Reading makefile recipes can be difficult because they're a noisy mix of make and
shell code that GNU make has to preprocess before anything is handed to the shell.
A rule with 60 lines of recipes could be intimidating, even if most of those lines
look like comments, so if you're relatively new to GNU make your first job probably
should be to organize recipe lines into disjoint groups. Start at the first line of
the rule's recipes and only stop collecting consecutive lines when you run into one
that doesn't end with a backslash character.
keep mentally collecting consecutive lines until you find one
that doesn't end with a backslash character.




 the first thing you

If you don't have much experience with GNU make, a rule with 60 lines that  of recipes could be intimidating, so
 a 60 line recipe 
 is unusual, even if most of the lines are comments, but the first
thing you probably should do





Perhaps the easiest way to start is to mentally organize a rule's recipe lines into
disjoint groups that are glued together by 

looking for
Perhaps the best way to start to group recipe lines together by
to look at the last character in each line of a
rule's recipes. 
If you're relatively new to make, my recommendation is that your first step should


If you're relatively new to make, my recommendation is that your first step should
be to mentally split the rule's recipes into groups. Start with the first line and
keep adding consecutive lines to that "group" when the current line (i.e., the one
you're looking at) 
with a backslash. 

    Start 
    group[1] = line[
    while 
    current_line = first_line
    while current_line 



when you want to understand a rule's recipes, like the 60 line monster that you're
hopefully looking at, is to bust it into pieces by checking at the last character on
each line.

 you're confronted with a rule that 
If you're new to GNU make you're probably overwhelmed by a 60 line recipe, even if
most of the lines are comments, 

Probably
A 60 line recipe is unusual, even if most of the lines are comments, but the first
thing you probably should do

but if you're
not sure what's happening tackle one line at a time, starting at the first line.


Reading makefile recipes can be difficult because they're a strange mix of make and
shell code that GNU make has to preprocess before anything is handed to the shell.
A 60 line recipe is unusual, even if most of the lines are comments, but if you're
not sure what's happening tackle one line at a time, starting at the first line.

### Comments

Makefiles contain text that's either consumed by make or just preprocessed before
it's handed to the shell. Both programs (GNU make and the shell) support comments
that start with a '#' character and continue to the end of the line, but a comment
in a makefile that ends with an unescaped backslash is continued on the next line.

It's a difference between make and shell comments that's documented in the manual,
but isn't something that's used in any of the makefiles in this repository.

### Comment Problems

More annoying is what happens when you add a comment to the end of a line, like
the definition of a makefile variable. For example, adding a short comment on the
same line as the variable definition

    KEY := VALUE                # this is used to ...

could often be helpful. Since there's no mention in the manual about what happens
here, assuming that the word VALUE is assigned to the makefile variable KEY would
be perfectly reasonable. Unfortunately, what actually happens is all of the white
space between the end of the variable assignment and the start of the comment also
ends up in the definition of KEY.

Using square brackets to mark the ends of strings, you probably would expect KEY
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

