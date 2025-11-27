## Bytedump - Bash Version

This is a big bash script, filled with comments, that basically just postprocesses
the output of xxd. Even though it works (on Linux) it's definitely not supposed to
be used to dump the bytes in anything other than very small files. Instead, my hope
is that parts of the source code might be useful to people writing bash scripts. I
think there are some worthwhile things in the script - maybe some of those comments
will help you find and follow them.

### Why Bash?

Several years ago I wanted a quick way to illustrate what's stored on a hard drive
(i.e., ones and zeros) without having to resort to the hex or octal representation
of bytes. xxd's "bits" dump (the one you get using its -b option) was close and one
sed command easily removed all of the distracting addresses and ASCII text from the
output.

That simple xxd postprocessing gradually turned into a small bash script that grew
as I kept finding little things to adjust in xxd's output. Eventually I decided to
spend some time cleaning the script up, not because it had any value, but instead
because I thought it might be useful (just to me) as a "template" for bash scripts
that I occasionally write for my own systems. The whole thing turned into a puzzle
and a real challenge - the bytedump-bash.sh script in this directory is my solution
to that puzzle.

### Where Did It Come From?

This is a trivially modified version of the bytedump bash script that was stored in
my public GitHub repository

    https://github.com/rich-drechsler/bytedump-bash

If you're familiar with that old repository you'll probably notice the bash script
that generated the dump is now named bytedump-bash.sh. The change was made because
this repository includes at least different two implementations of bytedump and it
uses explicit "suffixes", like "-bash" or "-java", that are attached to executables
to make sure their names convey some useful information and don't collide.

