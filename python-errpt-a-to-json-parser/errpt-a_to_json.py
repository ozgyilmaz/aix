from pyparsing import *
import os
import json

###################################
# regex definitions               #
###################################

# regex for string consisting of at least two dots
# used for key/value pairs of VPD blocks
regex_dotted_line       = Suppress(Regex("\.{2,}"))
# definition for separator dashed line, consisting of 75 dashes
regex_dashed_line       = Regex( r"-{75}" )
# read everything until a dashed line, consisting of 75 dashes
# used to determine the end of description
regex_until_dashed_line = Regex( r"(.|\n)*?---------------------------------------------------------------------------" )
# read everything until EOF
# used to determine the end of description
regex_until_eof         = Regex( r"(.|\n)*" )


###################################
# VPD definition                  #
###################################

# vpd keys consist of alphanumeric, space and some special chars.
# it may also contain a single dot, like: "Device Specific.(Z0)"
vpd_key     = Combine(Word(alphanums + " ") + ('.' + Word(alphanums+"("+")")) * (0,1))
# vpd values consist of alphanumeric chars
vpd_value   = Word(alphanums)
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
info_value          = Word(alphanums+" "+":"+"+"+"_"+"."+"-") + Optional(vpd_grammar)
# an info key/value pair contains a "key" and a "value"
info_line           = Dict( Group( info_key + info_value ) )
# description has a special format... it doesnt have semicolon, also it's not
# clear where it finishes. 
# "probable cause", "user causes" etc will be parsed in next version
# description (as a whole test containing sub titles like probable cause etc)
# may end with a dashed line, or with EOF.
info_description    = Suppress(Literal("Description")) + (regex_until_dashed_line|regex_until_eof).setResultsName('Description')
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
    # find raw "errpt -a" output files (with extension *.raw)
    raw_files = [filename for filename in os.listdir('.') if (filename.endswith("raw"))]
    # loop raw "errpt -a" files
    for raw_file in raw_files:
        # open raw file
        with open(raw_file,"r") as f:
            # parse raw file and put the result set in result variable
            result = grammar.parseString(f.read(), parseAll=True).as_dict()
        # open json file for write
        with open(os.path.splitext(raw_file)[0]+".json", "w") as f:
            # dump the "result" set as json
            json.dump(result, f, indent=4)

if __name__ == "__main__":
    main()