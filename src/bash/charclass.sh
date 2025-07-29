#!/bin/bash
#
# Used this script to generate the hex mappings that enumerated the bytes matched
# by the "character class" selector tokens implemented in the function (or method)
# that parsed those tokens. In the bash version of bytedump the function is named
# ByteSelector, so that's where you'll find the hex mappings.
#
# There were a few small disagreements (and inconsistencies) in several character
# classes, and ultimately I decided to go with the mappings generated using Java's
# regular expressions. This script built the original mappings using bash regular
# expressions and was it included in the source package to document how those hex
# mappings were built. The new Java implementation of bytedump includes debugging
# code that's now used to build the hex mappings. I decided to leave this script
# in the source code package, even though its output is no longer used.
#

matchedbytes=()
bytes="TRUE"
missed=""
matched=""

while (( $# > 0 )); do
    case "$1" in
          +bytes) bytes="TRUE";;
          -bytes) bytes="";;
        +matched) matched="TRUE";;
        -matched) matched="";;
         +missed) missed="TRUE";;
         -missed) missed="";;
              --) shift; break;;
               *) break;;
    esac
    shift
done

if [[ $1 =~ ^[[:blank:]]*(alnum|alpha|blank|cntrl|digit|graph|lower|print|punct|space|upper|xdigit)[[:blank:]]*$ ]]; then
    charclass="[:${BASH_REMATCH[1]}:]"
    shift
    for range in "${@:-00-FF}"; do
        if [[ $range =~ ^(([[:xdigit:]]+)([-]([[:xdigit:]]+))?)$ ]]; then
            first="16#${BASH_REMATCH[2]}"
            last="16#${BASH_REMATCH[4]:-${BASH_REMATCH[2]}}"
            for (( index = first; index <= last; index++ )); do
                state=""
                hex=$(printf "%.2X" "$index")

                #
                # Bash can't handle null bytes in strings and command substitution
                # tosses trailing newlines, so deal with them separately.
                #
                case "${hex^^}" in
                    00) char="";;
                    0A) char=$'\n';;
                     *) char=$(printf "%b" "\u00${hex}");;
                esac

                if [[ $char =~ ^[${charclass}]$ ]]; then
                    state="${matched:+"TRUE"}"
                    matchedbytes[index]="$hex"
                elif [[ $charclass == "[:cntrl:]" && $index == "0" ]]; then
                    state="${matched:+"TRUE"}"
                    matchedbytes[index]="$hex"
                else
                    state="${missed:+"FALSE"}"
                fi

                if [[ -n $state ]]; then
                    if [[ ${char} =~ [[:print:]] ]]; then
                        printf "HEX=%s, CHAR=%s: %s\n" "$hex" "$char" "$state"
                    else
                        printf "HEX=%s, CHAR=%s: %s\n" "$hex" "^$hex" "$state"
                    fi
                fi
            done
        fi
    done
fi

if [[ -n $bytes ]]; then
    if (( ${#matchedbytes[@]} > 0 )); then
        sep=""
        for (( index = 0; index < 256; index++ )); do
            if [[ -n ${matchedbytes[$index]} ]]; then
                first="$index"
                for (( last=index; index < 256; index++ )); do
                    if [[ -n ${matchedbytes[$index]} ]]; then
                        last=$index
                    else
                        break
                    fi
                done
                printf "%s%s" "$sep" "${matchedbytes[$first]}"
                if (( last > first )); then
                    printf -- "-%s" "${matchedbytes[$last]}"
                fi
                sep=" "
            fi
        done
        printf "\n"
    fi
fi

