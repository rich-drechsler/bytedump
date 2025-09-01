##
## A GNU makefile that can be used to manage the language specific bytedump versions
## listed in the SRCDIRS variables. It's really just a "helper" makefile that runs a
## small shell script that finds the makefiles that build things. Doing it this way
## (in a makefile) obviously isn't necessary, but it means makefiles are responsible
## for building everything, and I kind of like that consistency. Take a look at
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
# This makefile can be used to manage each of the bytedump applications named in
# the SRCDIRS variable. Each word in SCRDIRS must be the name of a directory that
# contains a file named Makefile that recognizes the following targets:
#
#         all - build the bytedump application in each directory that's listed
#               in SRCDIRS, but everything is left in those directories.
#
#               This is the first target in the makefile that doesn't start with
#               a period, so it's also the target that's built when there aren't
#               any targets mentioned on the command line. In other words
#
#                   make all
#
#               and
#
#                   make
#
#               accomplish exactly the same thing.
#
#     install - builds the bytedump applications named in SRCDIRS and installs
#               each one in the directory assigned to the INSTALLDIR variable.
#               That directory must exist, but any directories under it, like
#               bin or lib, will be created as needed.
#
#               Command line arguments that are handed to GNU make normally are
#               the targets that you want built, however an argument containing
#               an equal sign is treated as a variable assignment that overrides
#               any existing definition of that variable. For example,
#
#                   make INSTALLDIR=/tmp/bytedump install
#
#               will install everything in directory /tmp/bytedump, provided that
#               directory already exists.
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
MAKEFLAGS := --no-print-directory

.DELETE_ON_ERROR :

####################
#
# Variables
#
####################

INSTALLDIR := ../image
INSTALL := install

SOURCEDIRS := bash java

####################
#
# Rules
#
####################

all install clean clobber testfiles :
	@HERE="$${PWD}"; \
	INSTALLDIR="$(realpath $(INSTALLDIR))"; \
	if [ -d "$${INSTALLDIR}" ] || [ "$@" != "install" ]; then \
	    # \
	    # Loops though the source directories listed in SRCDIRS and uses the makefile \
	    # in each directory to build the target. Each directory should be a language \
	    # specific bytedump implementation with a makefile that recognizes all of the \
	    # targets of this rule. \
	    # \
	    for DIR in $(SOURCEDIRS); do \
	        if [ -d "$${DIR}" ] && [ -f "$${DIR}/$(MAKEFILE)" ]; then \
		    cd "$${DIR}"; \
		    echo "==== Making $@ in directory $${PWD} ===="; \
		    # \
		    # Exiting with a zero status if the following $(MAKE) call fails is done \
		    # to reduce noise. Everything needed to track the problem down has already \
		    # been explained to the user and there's nothing useful this instance of \
		    # make can add, so we just exit and pretend it all worked. \
		    # \
		    $(MAKE) -f "$(MAKEFILE)" INSTALLDIR="$${INSTALLDIR}" "$@" && echo || exit 0; \
		    cd "$${HERE}"; \
	        fi; \
	    done; \
	else \
	    if [ "$(INSTALLDIR)" ]; \
		then echo "Skipping install because installation directory '$(INSTALLDIR)' doesn't exist"; \
	        else echo "Skipping install because no installation directory is set"; \
	    fi; \
	fi

