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
# This makefile manages the java version of bytedump. It understands the following
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

JAR := jar
JAVAC := javac
JAVACFLAGS := -Xlint -Xdiags:verbose
JDEPS := jdeps

#
# A second Java implementation of bytedump could be packaged in this jar file and
# launched by its own bash script that's listed in COMMAND_SCRIPTS. New launchers
# are all built by making a few simple changes to the launcher_template.sh script.
# All you should have to do is add the name of that class file to MAINFILES and
# also include an appropriately named "help" file to this directory.
#

MAINFILES := ByteDump.java
HELPFILES := $(MAINFILES:.java=.help)
JAVAFILES := $(MAINFILES) AttributeTables.java RegexManager.java StringMap.java StringTo.java Terminator.java
CLASSFILES_JAVA := $(JAVAFILES:.java=.class)
CLASSFILES_INTERNAL := ByteDump$$1.class Terminator$$ExitError.class Terminator$$ExitException.class

JARFILE := bytedump-java.jar
JARCLASSES := $(CLASSFILES_JAVA) $(CLASSFILES_INTERNAL)

COMMAND_LAUNCHER := launcher_template.sh	# custom Java app launcher

#
# The substitutions here are undone (to get the Java class name) in the rule that
# builds command scripts from the Java app launcher. Overkill, but it should just
# work if a ByteDump.java class file is ever added to MAINFILES.
#

COMMAND_SCRIPTS := $(subst .java,-java,$(subst ByteDump,bytedump,$(subst Bash,_bash,$(MAINFILES))))

TESTFILES := sorted_bytes

####################
#
# Rules
#
####################

all : jar commands
	@# A comment eliminates make's "Nothing to be done ..." message.

clean :
	rm -f *.class
	@if [ "$(TESTFILES)" ]; then \
	    echo "rm -f $(TESTFILES)"; \
	    rm -f $(TESTFILES); \
	fi

clobber : clean
	rm -f $(JARFILE) $(COMMAND_SCRIPTS)

install : all
	@set -e; \
	if [ -d "$(INSTALLDIR)" ]; then \
	    echo "++++ Installing files under directory $(INSTALLDIR) ++++"; \
	    echo '$(INSTALL) -d -m755 "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -d -m755 "$(INSTALLDIR)/bin"; \
	    echo '$(INSTALL) -m755 $(COMMAND_SCRIPTS) "$(INSTALLDIR)/bin"'; \
	    $(INSTALL) -m755 $(COMMAND_SCRIPTS) "$(INSTALLDIR)/bin"; \
	    echo '$(INSTALL) -d -m755 "$(INSTALLDIR)/lib"'; \
	    $(INSTALL) -d -m755 "$(INSTALLDIR)/lib"; \
	    echo '$(INSTALL) -m644 $(JARFILE) "$(INSTALLDIR)/lib"'; \
	    $(INSTALL) -m644 $(JARFILE) "$(INSTALLDIR)/lib"; \
	else \
	    if [ "$(INSTALLDIR)" ]; \
	        then echo "Skipping install because installation directory '$(INSTALLDIR)' doesn't exist"; \
		else echo "Skipping install because no installation directory is set"; \
	    fi; \
	fi;

testfiles : $(TESTFILES)
	@# A comment eliminates make's "Nothing to be done ..." message.

#
# Several convenient rules.
#

jar : $(JARFILE)

classes : $(JARCLASSES)

commands : $(COMMAND_SCRIPTS)

#
# Rules that do the real work.
#

$(JARFILE) : $(JARCLASSES) $(HELPFILES) $(MAKEFILE)
	@echo "++++ Building $@ ++++"
	$(JAR) cf '$@' *.class *.help
	@$(JAR) tf '$@' | sed -e '/^META/d' -e 's/^/    added: /'
	$(JAR) i '$@'
	@echo

$(JARCLASSES) : $(JAVAFILES) $(MAKEFILE)
	@echo "++++ Building Class Files ++++"
	@rm -f *.class
	$(JAVAC) $(JAVACFLAGS) $(JAVAFILES)
	@echo

$(COMMAND_SCRIPTS) : $(COMMAND_LAUNCHER) $(MAKEFILE)
	@echo "++++ Building $@ ++++"
	sed \
	    -e 's#^declare[ ][ ]*SCRIPT_MAINCLASS=.*#declare SCRIPT_MAINCLASS="$(subst -java,,$(subst bytedump,ByteDump,$(subst _bash,Bash,$@)))"#' \
	    -e 's#^declare[ ][ ]*SCRIPT_JARNAME=.*#declare SCRIPT_JARNAME="$(JARFILE)"#' \
	    -e 's#^declare[ ][ ]*SCRIPT_JARPATH=.*#declare SCRIPT_JARPATH="../lib:."#' \
	< $< > $@
	chmod a+x $@
	@echo

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

####################
#
# An Experiment
#
####################

#
# A hastily written rule that tries to use the jdeps Java class dependency analyzer
# to look for classes that, for some reason, may not be included in $(JARFILE). It
# uses grep to identify possible problems in the jdeps output, but it's an approach
# that probably has only been tested on output produced by the 1.8 version of jdeps.
#

validate : $(JARFILE)
	@if command -v "$(JDEPS)" >/dev/null; then \
	    echo "++++ Validating $< ++++"; \
	    NOT_FOUND=$$($(JDEPS) -verbose $< | grep '[^ ][^ ]*[ ][ ]*[ ]->[ ][^ ][^ ]*[ ][ ]*not found'); \
	    if [ -n "$${NOT_FOUND}" ]; then \
		echo "    $< contains unresolved references:"; \
		echo "$${NOT_FOUND}" | sed -e 's/^  *//' -e 's/^/        /' -e's/  *->/ ->/' -e 's/  *not found//'; \
		exit 1; \
	    else \
		echo "    $< - validated"; \
		echo; \
	    fi; \
	fi

