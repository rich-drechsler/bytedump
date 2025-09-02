#!/bin/bash
#
# Copyright (C) 2025 Richard L. Drechsler (https://github.com/rich-drechsler/bytedump)
# SPDX-License-Identifier: MIT
#
# This is a bash script that can be used to launch Java applications. There's a
# template file (named launcher_template.sh) that's designed to be stream edited
# using a few simple sed commands and renamed when the Java application is built.
# The three variables that applications should set when they're built are:
#
#   SCRIPT_MAINCLASS
#       Name of the Java class to launch after the jar file is found. There's
#       no reasonable default and I decided against using the environment, so
#       this variable must be set when the application is built.
#
#   SCRIPT_JARNAME
#       The basename of the application's jar file, which must end in a ".jar"
#       suffix. There's no reasonable default and the environment isn't used,
#       so this variable must be set when the application is built.
#
#   SCRIPT_JARPATH
#       Colon separated list of paths used to find a jar file. Relative paths
#       in SCRIPT_JARPATH start in the directory where this script was found;
#       absolute paths are used as written. The default is "../lib:.", which
#       I think is reasonable, but applications should probably always set it
#       when they're built.
#
# Despite appearences, this isn't a complicated bash script and the main idea is
# pretty simple. Canonicalize ${BASH_SOURCE[0]} in a way that resolves symlinks,
# use dirname to get the directory containing this script, and then look for the
# file named $SCRIPT_JARNAME using the colon separated list of directories that
# were assigned to SCRIPT_JARPATH when the Java application was built.
#
# There are a few special options that give you some control over this script.
# I haven't documented them or the restictions on where they have to appear on
# the command line. That means you'll have to read the Options function if you
# want to see what's available.
#
# There are two separate "Imported" blocks of code that you'll find at the end
# of this script. One is a trimmed down version of the error handling code that
# was used in the bash version of bytedump application. The other contains two
# functions that this script uses to generate canonical paths. I think both are
# worth a quick look.
#
# NOTE - this script won't work with the version of bash that comes with MacOS.
# The bash portability issues that I'm aware of are:
#
#     readarray builtin (bash 4.0 - 2009)
#       Used to split pathnames and colon separated directory lists into
#       pieces that are stored in an array. My guess is IFS and the read
#       builtin (using the -ra options) might also work in this script.
#
#     negative array indices (bash 4.3 - 2014)
#       Only used to access the last element in an array. In this script
#       that element's index always is 1 less than the number of elements
#       in that array, so this would be easy to fix. This won't work in a
#       sparse array.
#
#     parameter quoting (bash 4.4 - 2016)
#       Only needed in the debugging dump of the command line, so whether
#       that works or not isn't important. It also appears in the imported
#       path support functions, but this script never gets to that code.
#
# The first two should be easy to address and the third can be ignored. This
# isn't guaranteed to be a complete list - I'll leave MacOS porting to anyone
# who thinks it's worth the effort.
#

##############################
#
# Shellcheck Initialization
#
##############################

#
# These are file-wide shellcheck directives:
#
#   shellcheck disable=SC2034           # unused variable
#   shellcheck disable=SC2120           # references args, none passed
#
# To be effective they have to precede the script's first shell command, which is
# why they're here.
#

##############################
#
# Script Variables
#
##############################

#
# Debugging is enabled when SCRIPT_DEBUG is set to "TRUE", which is what happens
# when you use the --launcher-debug option.
#

declare SCRIPT_DEBUG="FALSE"

#
# Some reasonable defaults.
#

declare -r SCRIPT_DEFAULT_JAVA="java"
declare -r SCRIPT_DEFAULT_JARPATH="../lib:."

#
# Name of the program that this script calls to actually launch Java applications.
# It can be changed on the command line using the --launcher-java option.
#

declare SCRIPT_JAVA="${SCRIPT_DEFAULT_JAVA}"

#
# These variables are usually set when the package is built. SCRIPT_MAINCLASS and
# SCRIPT_JARNAME are required and there are no reasonable defaults, so the script
# aborts early (in the Setup function) if they're not defined.
#

declare SCRIPT_MAINCLASS=""
declare SCRIPT_JARNAME=""
declare SCRIPT_JARPATH="${SCRIPT_DEFAULT_JARPATH}"

#
# ${BASH_SOURCE[0]} is used to get the canonical path to this script. That path is
# split into its basename and dirname, which are stored in the SCRIPT_BASENAME and
# SCRIPT_DIRECTORY variables.
#

declare SCRIPT_FILE=""
declare SCRIPT_BASENAME=""
declare SCRIPT_DIRECTORY=""

#
# Once we know where this script lives we ask FindJar to look for the application's
# jar file using values that are assigned to SCRIPT_JARPATH and SCRIPT_DIRECTORY.
# The value assigned to SCRIPT_JARFILE, either by FindJar or the --launcher-jarfile
# option, will be the jar file that's used when the Java application is launched.
#

declare SCRIPT_JARFILE=""

#
# Strings in the SCRIPT_JAVA_OPTIONS array are supposed to be options that will be
# included in the command that launches Java. They can be added to the array using
# various --launcher-java-option options that are accepted in the Options function.
#

declare -a SCRIPT_JAVA_OPTIONS=();

#
# The number of command line arguments consumed as launcher options in the Options
# function ends up stored in SCRIPT_ARGUMENTS_CONSUMED. That value is used by Main
# to skip the arguments that Options accepted.
#

declare SCRIPT_ARGUMENTS_CONSUMED="0"

##############################
#
# Script Functions
#
##############################

Arguments() {
    #
    # Runs the application that's implemented in the $SCRIPT_MAINCLASS Java class, which
    # must be stored in the $SCRIPT_JARFILE jar file. The java command that launches the
    # application doesn't assume $SCRIPT_JARFILE is an executable jar file. Instead, it
    # builds a slightly more complicated java command that, among other things, sets the
    # CLASSPATH to the $SCRIPT_JARFILE and then asks java to run the $SCRIPT_MAINCLASS
    # class.
    #

    if [[ ${SCRIPT_DEBUG} == "TRUE" ]]; then
        printf "%s\n" "Java Command:"
        printf "    %s\n" "CLASSPATH=${SCRIPT_JARFILE@Q} ${SCRIPT_JAVA@Q} ${SCRIPT_JAVA_OPTIONS[*]@Q} -Dprogram.name=${SCRIPT_BASENAME@Q} ${SCRIPT_MAINCLASS@Q} ${*@Q}"
        printf "\n"
    fi >&2

    CLASSPATH="${SCRIPT_JARFILE}" "${SCRIPT_JAVA}" "${SCRIPT_JAVA_OPTIONS[@]}" -D"program.name=${SCRIPT_BASENAME}" "${SCRIPT_MAINCLASS}" "$@"
}

FindJar() {
    local directory
    local field
    local -a fields
    local jarfile
    local jarname
    local jarpath
    local status

    #
    # The first argument that's not one of the recognized options is the jar file that
    # we're supposed to find. That search is controlled by the -directory option, which
    # sets the starting point for relative pathname searches, and the -jarpath option,
    # which is used to set the colon separated list of directories where the jar file
    # could be located.
    #
    # Relative pathnames in that colon separated list always start at the directory set
    # by the -directory option. The first readable, regular file found ends the search.
    # Its canonical pathname is written to standard output and a zero status is returned
    # to the caller. Otherwise, nothing prints on standard output and a nonzero status
    # is returned to the caller. This function is only called once in this script, and
    # that call uses the -directory option to make sure relative seaches always start
    # in the directory where this script was found.
    #
    # NOTE - bash's readarray builtin is used to split $jarpath into components. Take a
    # look at
    #
    #     https://stackoverflow.com/questions/10586153/how-to-split-a-string-into-an-array-in-bash
    #
    # and the wonderful answer posted by bgoldst for more details. It's a long post, so
    # skip to the "Wrong answer #8" heading and start reading from there if you want to
    # understand how readarray is used in this function.
    #

    status="1"
    directory=""
    jarpath="${SCRIPT_DEFAULT_JARPATH}"

    while (( $# > 0 )); do
        case "$1" in
            -directory=?*)
                directory="${1#-directory=}";;

            -jarpath=?*)
                jarpath="${1#-jarpath=}";;

            --) shift; break;;
             *) break;;
        esac
        shift
    done

    jarname="$1"

    if [[ $jarname == *.jar ]] && [[ -n $directory ]]; then
        #
        # Jar file names that don't start with "/" are resolved using the colon separated
        # components of $jarpath. Components that aren't empty and don't start with a "/"
        # are eventually combined with $directory before being used to build the candidate
        # jar file path.
        #
        if [[ $jarname =~ ^[^/] ]]; then
            fields=()
            readarray -td: fields <<< "${jarpath}:"
            unset "fields[-1]"          # last field comes from <<< appended newline
        else
            fields=("")
        fi

        for field in "${fields[@]}"; do
            if [[ -n $field ]]; then
                if [[ $field =~ ^[^/] ]]; then
                    field="${directory}/${field}"           # changes field
                fi
                #
                # No reason to worry about trailing newlines here - at this point we know the
                # name of the file we're looking for ends in ".jar".
                #
                jarfile="$(PathCanonical "${field}/${jarname}")"
                if [[ -f "$jarfile" && -r "$jarfile" ]]; then
                    printf "%s" "$jarfile"
                    status="0"
                    break
                fi
            fi
        done
    fi

    return "$status"
}

Initialize() {
    #
    # Initialization that happens after all of the command line launcher options are
    # processed. At this point SCRIPT_JARFILE will usually be empty and FindJar will
    # have to locate the application's jar file. The only time FindJar won't be used
    # is if SCRIPT_JARFILE was set by the --launcher-jarfile command line option.
    #

    SCRIPT_JAVA="${SCRIPT_JAVA:-${SCRIPT_DEFAULT_JAVA}}"
    SCRIPT_JARPATH="${SCRIPT_JARPATH:-${SCRIPT_DEFAULT_JARPATH}}"
    SCRIPT_JARFILE="${SCRIPT_JARFILE:-$(FindJar -directory="${SCRIPT_DIRECTORY}" -jarpath="${SCRIPT_JARPATH}" "--" "${SCRIPT_JARNAME}")}"

    #
    # Everything's set, so dump the important variables if we're debugging. Do it now
    # so their values are printed before the final checks.
    #

    if [[ ${SCRIPT_DEBUG} == "TRUE" ]]; then
        printf "%s\n" "Script Variables:"
        printf "    SCRIPT_FILE=%s\n" "$SCRIPT_FILE"
        printf "    SCRIPT_DIRECTORY=%s\n" "$SCRIPT_DIRECTORY"
        printf "    SCRIPT_BASENAME=%s\n" "$SCRIPT_BASENAME"
        printf "    SCRIPT_JARNAME=%s\n" "$SCRIPT_JARNAME"
        printf "    SCRIPT_JARPATH=%s\n" "$SCRIPT_JARPATH"
        printf "    SCRIPT_JARFILE=%s\n" "$SCRIPT_JARFILE"
        printf "    SCRIPT_JAVA=%s\n" "$SCRIPT_JAVA"
        printf "\n"
    fi >&2

    if [[ -n "$SCRIPT_JARFILE" ]]; then
        if [[ -f "$SCRIPT_JARFILE" && -r "$SCRIPT_JARFILE" ]]; then
            if ! command -v "${SCRIPT_JAVA}" >/dev/null 2>&1; then
                Error "can't find java application launcher $(Delimit "${SCRIPT_JAVA}")"
            fi
        else
            Error "can't access jar file $(Delimit "${SCRIPT_JARFILE}")"
        fi
    else
        Error "can't find jar file $(Delimit "${SCRIPT_JARNAME}") using directory $(Delimit "${SCRIPT_DIRECTORY}") and search path $(Delimit "${SCRIPT_JARPATH}")"
    fi
}

Main() {
    #
    # Runs a Java application that's packaged in a jar file.
    #

    Setup
    Options "$@"
    shift "$((SCRIPT_ARGUMENTS_CONSUMED))"      # skip over the --launcher options
    Initialize
    Arguments "$@"
}

Options() {
    local arg
    local argc
    local optarg

    #
    # Handles special options that can be used for low level control of what happens
    # in this script. Those options are only recognized at the start of the argument
    # list and right now all of them must start with the "--launcher-" prefix.
    #
    # An argument that doesn't look like a launcher option terminates the loop. That
    # argument, and all the arguments that follow it, will eventually be handed to
    # the Java class file that implements the Java application. There's no explicit
    # way to mark the end of the launcher options - the first argument that's not a
    # recognized launcher option (even "--") ends this loop.
    #

    argc="$#"

    while (( $# > 0 )); do
        arg="$1"
        if [[ $arg =~ ^("--launcher-"[^=]*)([=](.+)){0,1}$ ]]; then
            #
            # Argument looks like a special "launcher" option.
            #
            optarg="${BASH_REMATCH[3]}"
            case "$arg" in
                --launcher-debug)
                    SCRIPT_DEBUG="TRUE";;

                --launcher-jarfile=?*)
                    SCRIPT_JARFILE="$optarg";;

                --launcher-jarpath=?*)
                    SCRIPT_JARPATH="$optarg";;

                --launcher-java=?*)
                    SCRIPT_JAVA="$optarg";;

                --launcher-java-option=-verbose:?*)
                    SCRIPT_JAVA_OPTIONS+=("$optarg");;

                --launcher-java-option=-X?*)
                    SCRIPT_JAVA_OPTIONS+=("$optarg");;

                 *) Error "launcher option $(Delimit "${arg}") is not recognized";;
            esac
        else
            break;
        fi
        shift
    done

    SCRIPT_ARGUMENTS_CONSUMED=$((argc - $#))
}

Setup() {
    #
    # Initialization and checks that can happen before the command line options are
    # processed. The makefile that built this application is supposed to initialize
    # important global variables, like SCRIPT_MAINCLASS and SCRIPT_JARNAME. If any
    # of the important variables aren't properly set, something's definitely wrong
    # and we'll quit.
    #

    if [[ -n $SCRIPT_MAINCLASS ]]; then
        if [[ -n $SCRIPT_JARNAME ]]; then
            if [[ $SCRIPT_JARNAME =~ ^[^/]+[.]jar ]]; then
                SCRIPT_JAVA="${SCRIPT_JAVA:-java}"
                SCRIPT_FILE="$(PathCanonical "${BASH_SOURCE[0]}")"
                if [[ -f $SCRIPT_FILE && -r $SCRIPT_FILE && -x $SCRIPT_FILE ]]; then
                    #
                    # $SCRIPT_FILE looks resonable, so remember its dirname and basename.
                    #
                    SCRIPT_DIRECTORY="$(command -p dirname "$SCRIPT_FILE")"
                    SCRIPT_BASENAME="$(command -p basename "$SCRIPT_FILE")"
                else
                    InternalError "file $(Delimit "${SCRIPT_FILE}") doesn't look like a bash script"
                fi
            else
                InternalError "jar file name $(Delimit "${SCRIPT_JARNAME}") is not valid"
            fi
        else
            InternalError "name of the jar file where java finds classes hasn't been assigned to SCRIPT_JARNAME"
        fi
    else
        InternalError "name of the class that java is supposed to launch hasn't been assigned to SCRIPT_MAINCLASS"
    fi
}

##############################
#
# Helper Functions
#
##############################

Delimit() {
    #
    # A trivial function that joins it's arguments using one space, surrounds that
    # string with double quotes, and prints it on standard output. It's currently
    # only used to visually isolate the cause of an error from its explanation in
    # error messages.
    #

    IFS=" " printf '"%s"\n' "$*"
}

##############################
#
# Path Support - Imported
#
##############################

#
# A few path related functions imported from a private bash library. They're very
# old, never used much, and I honestly don't recall how thorough the testing was,
# but all of the imported functions seem to work on Linux. PathCanonicalBash is a
# brute force implementation that was written as a fallback that's automatically
# called by PathCanonical if the realpath command misbehaves.
#

PathCanonical() {
    local arg
    local base64
    local path
    local paths
    local quote
    local status
    local suffix
    local terminated

    #
    # Returns the canonical path representation of the non-option arguments that
    # has . and .. resolved, consecutive slashes replaced by one slash, and all
    # symlinks resolved. The canonical paths are separated from each other by
    # a single newline; all null arguments are ignored. The first try is GNU's
    # realpath command, but if that fails the "brute force" bash implementation
    # that you'll find in the PathCanonicalBash function is used.
    #
    # Trailing newlines in file names pose a problem when our answer is handed
    # back to the caller via command substitution, because all newlines at the
    # end of the last (or the only) file name will always be stripped by bash.
    # There's lots of talk about it on stackoverflow and stackexchange - take a
    # look at
    #
    #     https://stackoverflow.com/questions/16991270/newlines-at-the-end-get-removed-in-shell-scripts-why
    #
    # if you're curious about the issues and possible solutions. What's done in
    # this function pretty much just follows the suggestion that you'll find in
    # the answer posted by Stephane Chazelas. In addition, when this function is
    # called with the +terminate option a period is appended to the string that's
    # written to standard output. However, that forces extra work on the caller,
    # so that's why +terminate is required to trigger the protection.
    #
    # Right now, trailing newlines in the pathname we generate is considered an
    # error when there's no encoding, quoting, or suffix to protect them (i.e.,
    # +base64, +quote, or +terminate weren't used). When that happens nothing is
    # written to standard output and we return a non-zero status (currently 2)
    # to the caller as a warning about the trailing newlines. Eventually expect
    # we could take a look at $BASH_SUBSHELL, because a zero value should mean
    # we weren't called using command substitution - maybe later.
    #
    # NOTE - using long GNU style options when realpath is called is intentional
    # and hopefully causes realpath to fail when those options aren't supported.
    # If that happens PathCanonicalBash gets a chance to canonicalize the path.
    #

    base64="FALSE"
    paths=""
    quote="FALSE"
    status="0"
    suffix=""

    while (( $# > 0 )); do
        case "$1" in
               +base64) base64="TRUE";;
               -base64) base64="FALSE";;
                +quote) quote="TRUE";;
                -quote) quote="FALSE";;
            +terminate) suffix=".";;
            -terminate) suffix=;;
                    --) shift; break;;
                     *) break;;
        esac
        shift
    done

    while (( $# > 0 )); do
        arg="$1"
        if [[ -n $arg ]]; then
            path=""
            if terminated="$(command -p realpath --canonicalize-missing --physical -- "$arg" 2>/dev/null && echo .)"; then
                path="${terminated%??}"
            elif terminated="$(PathCanonicalBash +terminate -- "$arg" 2>/dev/null)"; then
                path="${terminated%?}"
            else
                status="$?"
                break
            fi
            path="${path:-/}"

            if [[ $quote == "TRUE" ]]; then
                path="${path@Q}"                # requires bash 4.4 and later
            fi
            if [[ $base64 == "TRUE" ]]; then
                path="$(printf "%s" "$path" | command -p base64 --wrap=0 2>/dev/null)"
            fi

            paths+="${paths:+$'\n'}${path}"
        fi
        shift
    done

    if (( status == 0 )); then
        if [[ -n $paths ]]; then
            if [[ $quote == "TRUE" ]] || [[ $paths != *$'\n' ]] || [[ -n $suffix ]]; then
                printf "%s" "${paths}${suffix:-$'\n'}"
            else
                status="2"
            fi
        fi
    fi

    return "$status"
}

PathCanonicalBash() {
    local arg
    local base64
    local -a components
    local element
    local link
    local path
    local paths
    local -a pieces
    local quote
    local status
    local suffix
    local target

    #
    # This is a "brute force" bash version that can be used on its own, but it's
    # also automatically used (by PathCanonical) when the realpath command isn't
    # available or it exits with a non-zero status.
    #
    # NOTE - see the comments in PathCanonical for a more detailed description of
    # what's supposed to happen in this function.
    #

    base64="FALSE"
    path=""
    paths=""
    quote="FALSE"
    status="0"
    suffix=""

    while (( $# > 0 )); do
        case "$1" in
               +base64) base64="TRUE";;
               -base64) base64="FALSE";;
                +quote) quote="TRUE";;
                -quote) quote="FALSE";;
            +terminate) suffix=".";;
            -terminate) suffix=;;
                    --) shift; break;;
                     *) break;;
        esac
        shift
    done

    while (( $# > 0 )); do
        arg="$1"
        if [[ -n $arg ]]; then
            #
            # Need to start with an absolute path if we expect to handle symlinks
            # using readlink (without any options) and return an absolute path to
            # the caller. Not relying on readlink options, like --canonicalize or
            # -f, should let us assume that a nonzero return from readlink means
            # the argument wasn't a working symlink and not a complaint about an
            # option.
            #
            if [[ $arg =~ ^[/] ]]; then
                target="${arg}"
            else
                #
                # No reason to get fancy here. All symlinks are supposed to be
                # resolved, so we can prepend $PWD and just let the code handle
                # the symlinks (assuming that code is correct).
                #
                target="${PWD}/${arg}"          # $(pwd) trims trailing newlines!!
            fi

            pieces=()
            readarray -td/ pieces <<< "${target}/"
            unset "pieces[-1]"                  # toss newline added by <<<

            components=()
            path=""
            for element in "${pieces[@]}"; do
                if [[ -n $element ]]; then
                    if [[ $element == ".." ]]; then
                        if (( ${#components[@]} > 0 )); then
                            path="${path%"/${components[-1]}"}"
                            unset "components[-1]"
                        fi
                    elif [[ $element != "." ]]; then
                        if link="$(command -p readlink "$path/${element}" 2>/dev/null && echo .)"; then
                            link="${link%??}"
                            link="${link:-/}"
                            if [[ $link =~ ^/ ]]; then
                                path="$(PathCanonicalBash "$link")"
                                readarray -td/ components <<< "${path:1}/"
                                unset "components[-1]"
                            else
                                path="$(PathCanonicalBash "$path/$link")"
                                readarray -td/ components <<< "${path:1}/"
                                unset "components[-1]"
                            fi
                        elif [[ -L "$path/${element}" ]]; then
                            #
                            # If anything goes wrong readlink apparently always seems to exit
                            # with status 1. In this case the readlink failure could have been
                            # caused by a symlink loop, permissions, or other issues, so we set
                            # the status to 2 and break out of the loop.
                            #
                            status="2"
                            break
                        else
                            #
                            # Wasn't a symlink so just "append" element to the path.
                            #
                            path+="/${element}"
                            components+=("${element}")
                        fi
                    fi
                fi
            done
            if (( status == 0 )); then
                path="${path:-/}"

                if [[ $quote == "TRUE" ]]; then
                    path="${path@Q}"                # requires bash 4.4 and later
                fi
                if [[ $base64 == "TRUE" ]]; then
                    path="$(printf "%s" "$path" | command -p base64 --wrap=0 2>/dev/null)"
                fi

                paths+="${paths:+$'\n'}${path}"
            else
                break
            fi
        fi
        shift
    done

    if (( status == 0 )); then
        if [[ -n $paths ]]; then
            if [[ $quote == "TRUE" ]] || [[ $paths != *$'\n' ]] || [[ -n $suffix ]]; then
                printf "%s" "${paths}${suffix:-$'\n'}"
            else
                status="2"
            fi
        fi
    fi

    return "$status"
}

##############################
#
# Error Support - Imported
#
##############################

#
# These are stripped down versions of error handling functions that originally
# came from a private bash library that I occasionally use. What's been removed
# shouldn't affect this script, mostly because right now none of these functions
# are used in subshells.
#
# NOTE - I tried to be careful when I trimmed things down, but I rushed though it
# and didn't run lots of tests. This is bash code, so it's always possible I made
# careless mistakes.
#
# NOTE - find the bash implementation of the bytedump application if you want the
# full, unedited version (including all the comments) of the error handling code.
#

Error() {
    local exit
    local -a options

    exit="TRUE"
    options=()

    while (( $# > 0 )); do
        case "$1" in
            +exit) exit="TRUE";;
            -exit) exit="FALSE";;
               --) shift; break;;
               +*) options+=("$1");;
               -*) options+=("$1");;
                *) break;;
        esac
        shift
    done

    Message -tag="Error" -info=line -escapes -stderr "${options[@]}" +frame -- "$@"

    if [[ $exit == "TRUE" ]]; then
        if [[ $BASHPID != "$$" ]]; then
            kill -TERM $$
        fi
        exit 1
    fi
}

InternalError() {
    local -a options

    options=()

    while (( $# > 0 )); do
        case "$1" in
            --) shift; break;;
            +*) options+=("$1");;
            -*) options+=("$1");;
             *) break;;
        esac
        shift
    done

    Error -tag="InternalError" -info=location +exit "${options[@]}" +frame -- "$@"
}

Message() {
    local arg
    local -A caller
    local format
    local frame
    local info
    local message
    local optarg
    local output
    local prefix
    local suffix
    local tag
    local token

    caller=()
    format="%b\n"
    frame="0"
    info=""
    output="-stderr"
    prefix="$(command -p basename "${BASH_SOURCE[0]}")"
    suffix=""
    tag=""

    while (( $# > 0 )); do
        arg="$1"
        if [[ $arg =~ ^[-+]([^=]+)[=](.+)$ ]]; then
            optarg="${BASH_REMATCH[2]}"
        else
            optarg=""
        fi
        case "$arg" in
            +escapes)
                format="%b\n";;

            -escapes)
                format="%s\n";;

            +frame)
                frame=$((frame + 1));;

            -frame)
                frame="0";;

            -info)
                info="";;

            -info=?*)
                info="${optarg}";;

            -prefix)
                prefix="";;

            -prefix=?*)
                prefix="${optarg}";;

            -stderr)
                output="$arg";;

            -stdout)
                output="$arg";;

            -suffix)
                suffix="";;

            -suffix=?*)
                suffix="${optarg}";;

            -tag)
                tag="";;

            -tag=?*)
                tag="${optarg}";;

            --) shift; break;;
            +*) ;;
            -*) ;;
             *) break;;
        esac
        shift
    done

    message="$*"

    if [[ -n $message ]]; then
        if [[ -n "$info" ]]; then
            caller[LINE]="${BASH_LINENO[$frame]}"
            caller[FUNCTION]="${FUNCNAME[$((frame + 1))]}"
            caller[SOURCE]="${BASH_SOURCE[$((frame + 1))]}"

            for token in ${info//,/ }; do
                case "${token^^}" in
                    CALLER)
                        if [[ -n ${caller[LINE]} ]] && [[ -n ${caller[FUNCTION]} ]] && [[ -n ${caller[SOURCE]} ]]; then
                            tag="${tag:+${tag}] [}${caller[SOURCE]}; ${caller[FUNCTION]}; Line ${caller[LINE]}"
                        fi;;

                    FUNCTION)
                        if [[ -n ${caller[FUNCTION]} ]]; then
                            tag="${tag:+${tag}] [}${caller[FUNCTION]}"
                        fi;;

                    LINE)
                        if [[ -n ${caller[LINE]} ]]; then
                            tag="${tag:+${tag}] [}Line ${caller[LINE]}"
                        fi;;

                    LOCATION)
                        if [[ -n ${caller[LINE]} ]] && [[ -n ${caller[SOURCE]} ]]; then
                            tag="${tag:+${tag}] [}${caller[SOURCE]}; Line ${caller[LINE]}"
                        fi;;

                    SOURCE)
                        if [[ -n ${caller[SOURCE]} ]]; then
                            tag="${tag:+${tag}] [}${caller[SOURCE]}"
                        fi;;
                esac
            done
        fi

        message="${prefix:+${prefix}: }${message}${tag:+ [${tag}]}${suffix}"

        #
        # shellcheck disable=2059
        #
        case "${output}" in
            -stderr)
                printf -- "${format}" "${message}" 1>&2;;

            -stdout)
                printf -- "${format}" "${message}";;

             *) printf -- "${format}" "${message}" 1>&2;;
        esac
    fi
}

##############################
#
# Script Start
#
##############################

Main "$@"
exit $?

