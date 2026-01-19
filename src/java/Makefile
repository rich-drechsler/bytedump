##
## A makefile for the Java implementation of the bytedump program that was written
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
# This makefile manages the Java version of bytedump. It understands the following
# targets, which currently work in every makefile in this repository:
#
#         all - builds the java version of bytedump, but leaves everything in
#               this directory. The executable is named bytedump-java and it
#               should run if you point your shell at it.
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
#     install - builds the "all" target and then copies whatever's necessary to
#               the right place under the directory assigned to the INSTALLDIR
#               variable. That directory must exist, but any directories under
#               it, like bin or lib, will be created as needed.
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
#       clean - removes any files created by this makefile that aren't needed to
#               run this application.
#
#     clobber - removes all of the files created by this makefile, including the
#               ones needed to run this application.
#
#   testfiles - builds test files that might occasionally be useful.
#
#    validate - builds the "all" target and then checks the launcher script using
#               shellcheck and examines the jar file using jdeps.
#
# NOTE - even though ByteDump.java is the only working Java bytedump implementation,
# the makefile included in the original release anticipated different Java versions.
# Initially I just wanted to end up with a readable makefile, but I got sidetracked
# and unnecessarily complicated the makefile by trying to support "phantom" bytedump
# implementations. It was tricky code that I'm sure confused almost anyone who tried
# to follow it, so I backed it out and now ByteDump.java is the only implementation
# of bytedump this makefile can deal with.
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
SHELLCHECK := shellcheck

JAR := jar
JAVAC := javac
JAVACFLAGS := -Xlint -Xdiags:verbose
JDEPS := jdeps

MAINFILE := ByteDump.java
MAINCLASS := $(MAINFILE:.java=)
HELPFILE := $(MAINFILE:.java=.help)
JAVAFILES := $(MAINFILE) AttributeTables.java RegexManager.java StringMap.java StringTo.java Terminator.java
CLASSFILES := $(JAVAFILES:.java=.class)
CLASSFILES_INTERNAL := ByteDump$$1.class Terminator$$ExitError.class Terminator$$ExitException.class

JARFILE := bytedump-java.jar
JARCLASSES := $(CLASSFILES) $(CLASSFILES_INTERNAL)

BYTEDUMP-JAVA := bytedump-java

#
# This is the name of bash script template that's used to create the command that
# launches the Java version of bytedump. It's a generic Java launcher that should
# be easy to use elsewhere.
#

LAUNCHER_TEMPLATE := launcher_template.sh

#
# Only one test file to build and that's probably the way it will always be.
#

TESTFILES := sorted_bytes

####################
#
# Rules
#
####################

all : $(JARFILE) $(BYTEDUMP-JAVA)
	@# A comment to eliminate make's "Nothing to be done ..." message.

clean :
	rm -f -- *.class
	@if [ "$(TESTFILES)" ]; then \
	    echo "rm -f -- $(TESTFILES)"; \
	    rm -f -- $(TESTFILES); \
	fi

clobber : clean
	rm -f -- "$(JARFILE)" "$(BYTEDUMP-JAVA)"

install : all
	@set -e; \
	if [ -d "$(INSTALLDIR)" ]; then \
	    echo "++++ Installing files under directory $(INSTALLDIR) ++++"; \
	    echo '$(INSTALL) -d -m755 "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -d -m755 "$(INSTALLDIR)/bin"; \
	    echo '$(INSTALL) -m755 "$(BYTEDUMP-JAVA)" "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -m755 "$(BYTEDUMP-JAVA)" "$(INSTALLDIR)/bin"; \
	    echo '$(INSTALL) -d -m755 "$(INSTALLDIR)/lib"'; \
	    $(INSTALL) -d -m755 "$(INSTALLDIR)/lib"; \
	    echo '$(INSTALL) -m644 "$(JARFILE)" "$(INSTALLDIR)/lib"'; \
	    $(INSTALL) -m644 "$(JARFILE)" "$(INSTALLDIR)/lib"; \
	else \
	    if [ "$(INSTALLDIR)" ]; \
	        then echo "Skipping install because installation directory '$(INSTALLDIR)' doesn't exist"; \
		else echo "Skipping install because no installation directory is set"; \
	    fi; \
	fi;

testfiles : $(TESTFILES)
	@# A comment to eliminate make's "Nothing to be done ..." message.

validate : all
	@if command -v "$(SHELLCHECK)" >/dev/null; then \
	    echo "++++ Validating $(BYTEDUMP-JAVA) ++++"; \
	    echo '    $(SHELLCHECK) "$(BYTEDUMP-JAVA)"'; \
	    if $(SHELLCHECK) "$(BYTEDUMP-JAVA)"; then \
		echo "    $(BYTEDUMP-JAVA) - validated"; \
	    else \
		exit 1; \
	    fi; \
	fi
	@if command -v "$(JDEPS)" >/dev/null; then \
	    # \
	    # Uses the jdeps Java class dependency analyzer to look for classes that, \
	    # for some reason, may not be included in the jar file. grep is used to look \
	    # through the jdeps output, so nothing is guaranteed and it's probably only \
	    # been tested using the 1.8 version of jdeps. \
	    # \
	    echo "++++ Validating $(JARFILE) ++++"; \
	    NOT_FOUND=$$($(JDEPS) -verbose "$(JARFILE)" | grep '[^ ][^ ]*[ ][ ]*[ ]->[ ][^ ][^ ]*[ ][ ]*not found'); \
	    if [ -n "$${NOT_FOUND}" ]; then \
		echo "    $(JARFILE) contains unresolved references:"; \
		echo "$${NOT_FOUND}" | sed -e 's/^  *//' -e 's/^/        /' -e's/  *->/ ->/' -e 's/  *not found//'; \
		exit 1; \
	    else \
		echo "    $(JARFILE) - validated"; \
	    fi; \
	fi

#
# Rules that do the real work.
#

$(JARFILE) : $(JARCLASSES) $(HELPFILE) $(MAKEFILE)
	@echo "++++ Building $@ ++++"
	$(JAR) cf '$@' *.class *.help
	@$(JAR) tf '$@' | sed -e '/^META/d' -e 's/^/    added: /'
	$(JAR) i '$@'
	@echo

$(JARCLASSES) : $(JAVAFILES) $(MAKEFILE)
	@echo "++++ Building Class Files ++++"
	@rm -f -- *.class
	$(JAVAC) $(JAVACFLAGS) $(JAVAFILES)
	@echo

$(BYTEDUMP-JAVA) : $(LAUNCHER_TEMPLATE) $(MAKEFILE)
	@echo "++++ Building $@ ++++"
	sed \
	    -e 's#^declare[ ][ ]*SCRIPT_MAINCLASS=.*#declare SCRIPT_MAINCLASS="$(MAINCLASS)"#' \
	    -e 's#^declare[ ][ ]*SCRIPT_JARNAME=.*#declare SCRIPT_JARNAME="$(JARFILE)"#' \
	    -e 's#^declare[ ][ ]*SCRIPT_JARPATH=.*#declare SCRIPT_JARPATH="../lib:."#' \
	< '$<' > '$@'
	chmod a+x '$@'

####################
#
# Test Files
#
####################

#
# The sorted_bytes target builds a 256 byte file (named sorted_bytes) where each
# byte in the file contains the 8-bit binary representation of the byte's offset.
# It's a binary test file that was occasionally useful, but it's an easy file to
# build with a few lines of shell.
#

sorted_bytes : $(MAKEFILE)
	@echo "++++ Building the $@ test file ++++"
	@for msd in 0 1 2 3 4 5 6 7 8 9 A B C D E F; do \
	    for lsd in 0 1 2 3 4 5 6 7 8 9 A B C D E F; do \
		/bin/echo -en "\\x$${msd}$${lsd}"; \
	    done; \
	done > '$@'

