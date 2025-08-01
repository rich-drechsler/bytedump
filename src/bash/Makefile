##
## A makefile for the bash implementation of the bytedump program that was written
## for GNU make. Take a look at
##
##     https://www.gnu.org/software/make/manual/make.html
##
## if you want more information about GNU make. It's a big manual, and in the past
## I would occasionally use it as a reference, but today chatbots are the place to
## go for help with GNU make.
##
## A common complaint about makefiles is tab indentation that's required in recipes.
## I often use vim, and by default my .vimrc file tells vim to automatically expand
## tabs. That would break most makefiles, so I also include the line
##
##     autocmd FileType make setlocal noexpandtab
##
## in .vimrc to prevent tab expansion when vim decides I'm editing a makefile. You
## may have to deal with something similar whenever you edit makefiles.
##

####################
#
# Overview
#
####################

#
# This makefile manages the bash version of bytedump. It understands the following
# targets, which currently work in every makefile in this repository:
#
#         all - builds the bash version of bytedump, but leaves everything in
#               this directory. The executable is named bytedump-bash and it
#               should run if you point your shell at it.
#
#     install - builds the "all" target and then copies whatever's necessary to
#               the right place under the directory assigned to the INSTALLDIR
#               variable. That directory must exist, but any directories under
#               it, like bin or lib, will be created as needed.
#
#               Command line arguments that are handed to GNU make normally are
#               the targets that you want built, however an argument containing
#               an equal sign is treated as a variable assignment. For example,
#
#                   make INSTALLDIR=/tmp/bytedump install
#
#               will try to install everything in directory /tmp/bytedump.
#
#       clean - removes files created by this makefile that aren't needed to run
#               this application.
#
#     clobber - removes all of the files created by this makefile, including the
#               ones needed to run this application.
#
#   testfiles - builds test files that might occasionally be useful.
#

####################
#
# Setup
#
####################

MAKEFILE := $(lastword $(MAKEFILE_LIST))

.DELETE_ON_ERROR :

####################
#
# Variables
#
####################

ROOT := ..
INSTALLDIR := ../$(ROOT)/image
INSTALL := install

BYTEDUMP := bytedump-bash
TESTFILES := sorted_bytes

####################
#
# Rules
#
####################

all : $(BYTEDUMP)
	@# A comment eliminates make's "Nothing to be done ..." message.

clean :
	@if [ "$(TESTFILES)" ]; then \
	    echo "rm -f $(TESTFILES)"; \
	    rm -f $(TESTFILES); \
	fi

clobber : clean
	rm -f $(BYTEDUMP)

install : all
	@set -e; \
	if [ -d "$(INSTALLDIR)" ]; then \
	    echo "++++ Installing files under directory $(INSTALLDIR) ++++"; \
	    echo '$(INSTALL) -d -m755 "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -d -m755 "$(INSTALLDIR)/bin"; \
	    echo '$(INSTALL) -m755 $(BYTEDUMP) "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -m755 $(BYTEDUMP) "$(INSTALLDIR)/bin"; \
	else \
	    if [ "$(INSTALLDIR)" ]; \
	        then echo "Skipping install because installation directory '$(INSTALLDIR)' doesn't exist"; \
		else echo "Skipping install because no installation directory is set"; \
	    fi; \
	fi

testfiles : $(TESTFILES)
	@# A comment eliminates make's "Nothing to be done ..." message.

#
# Not using make's implicit .sh rule, but only because I wanted consistent "build
# messages" from makefiles.
#

$(BYTEDUMP) : $(BYTEDUMP).sh
	@echo "++++ Building $@ ++++"
	cat $< >$@
	chmod a+x $@

####################
#
# Test Files
#
####################

#
# The sorted_bytes target builds a 256 byte file (named sorted_bytes) where each
# byte in the file contains the 8-bit binary representation of the byte's offset.
#

sorted_bytes : $(MAKEFILE)
	@echo "++++ Building the $@ test file ++++"
	@for msd in 0 1 2 3 4 5 6 7 8 9 A B C D E F; do \
	    for lsd in 0 1 2 3 4 5 6 7 8 9 A B C D E F; do \
		/bin/echo -en "\\x$${msd}$${lsd}"; \
	    done; \
	done > "$@"

