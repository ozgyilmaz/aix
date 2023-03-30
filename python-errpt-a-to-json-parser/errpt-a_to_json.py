from pyparsing import *
import os
import json
import argparse
import sys

# Custom action to strip the values
def strip_value(tokens):
    return [token.strip() for token in tokens]

###################################
# regex definitions               #
###################################

# regex for string consisting of at least two dots
# used for key/value pairs of VPD blocks
regex_dotted_line       = Suppress(Regex("\.{2,}"))
# definition for separator dashed line, consisting of 75 dashes
regex_dashed_line       = Regex( r"-{75}" )
# new line
# if you want to suppress new line \n characters, you can put
# .suppress() at the end of the line. Like:
# NL = LineEnd().suppress()
NL = LineEnd()
# read everything until a dashed line (consisting of 75 dashes
# used to determine the end of description) or until EOF
# also suppress this dash line or EOF
# Thanks to PaulMcG
# https://stackoverflow.com/questions/75782477/how-to-use-pyparsing-for-multilined-fields-that-has-two-different-types-of-endin
dashed_separator = (("-" * 75) + NL | StringEnd()).suppress()

###################################
# VPD definition                  #
###################################

# vpd keys consist of alphanumeric, space and some special chars.
# it may also contain a single dot, like: "Device Specific.(Z0)"
vpd_key     = Combine(Word(alphanums + " ") + ('.' + Word(alphanums+"("+")")) * (0,1))
# vpd values consist of alphanumeric chars
vpd_value   = Word(alphanums+".")
# a vpd key/value pair contains a "key", some "dots" and a "value"
vpd_line    = Dict(Group(vpd_key + regex_dotted_line + vpd_value))
# vpd grammar definition. We need to find at least one key/value pair if we hit a "VPD:" keyword
vpd_grammar = OneOrMore(vpd_line)


###################################
# info definition                 #
###################################

# standard info key definition like LABEL, IDENTIFIER etc
info_key            = Combine(Word(alphanums+" "+"/") + Suppress(":"))
# value may have alphanumeric chars, space, some special chars etc
# value also may have the whole VPD information and that should be
# also parsed as key/value pairs
info_value          = rest_of_line.addParseAction(strip_value) + Optional(vpd_grammar)
# an info key/value pair contains a "key" and a "value"
info_line           = Dict( Group( info_key + info_value ) )
# description has a special format... it doesnt have semicolon, also it's not
# clear where it finishes. 
# "probable cause", "user causes" etc will be parsed in next version
# description (as a whole test containing sub titles like probable cause etc)
# may end with a dashed line, or with EOF.
info_description    = Combine(
    Suppress("Description" + NL)
    + ZeroOrMore(rest_of_line + NL, stop_on=dashed_separator)
).setResultsName('Description')

# info grammar sums of everything
info_grammar        = Group(Suppress(Optional(regex_dashed_line)) + OneOrMore(info_line) + info_description)

###################################
# final grammar                   #
###################################

# final grammar consists of one or more info grammars which mean errpt records
grammar = OneOrMore(info_grammar).setResultsName("Errpt Records")



###################################
# main definition                 #
###################################

def main():

    # parser definition for options, arguments etc.
    parser = argparse.ArgumentParser()
    # defines work directory. When given the script traverse all directories and sub directories
    # of work directory to find files with "raw" extension.
    # When not given, script parses the string provided by standart input. Like pipes:
    # errpt -a | errpt-a_to_json.py
    parser.add_argument("-w", "--workdir", help="Work directory", required=False)
    # When given the raw file is removed after the parse operation.
    parser.add_argument('-r', "--remove", action='store_true', required=False)
    args = parser.parse_args()
    # if workdir is given
    if args.workdir:
        # walk through args.workdir and find raw "errpt -a" output files (with extension *.raw)
        # process raw files when found.
        for root, dirs, files in os.walk(args.workdir):
            print(root)
            for file in files:
                if (file.endswith("raw")):
                    print("Parsing: " + os.path.join(root, file))
                    try:
                        with open(str(os.path.join(root, file)),"r") as f:
                            # parse raw file and put the result set in result variable
                            result = grammar.parseString(f.read(), parseAll=True).as_dict()
                    except Exception as e:
                        print("File: " + os.path.join(root, file))
                        print(e)
                        exit(1)
                    try:
                        # open json file for write
                        with open(os.path.splitext(os.path.join(root, file))[0]+".json", "w") as f:
                            # dump the "result" set as json
                            json.dump(result, f, indent=4)
                    except Exception as e:
                        print("File: " + os.path.join(root, file))
                        print(e)
                        exit(1)
                    else:
                        # remove parsed raw file
                        if args.remove:
                            if os.path.exists(os.path.join(root, file)):
                                os.remove(os.path.join(root, file))
    # if workdir is NOT given. that means the script will parse the standard input data
    # like piped data:
    # cat somefile | python errpt-a_to_json.py
    else:
        try:
            result = grammar.parseString(sys.stdin.read(), parseAll=True).as_dict()
            print(json.dumps(result, indent=4))
        except Exception as e:
            print("Screen dump error")
            print(e)
            exit(1)
                        

if __name__ == "__main__":
    main()
