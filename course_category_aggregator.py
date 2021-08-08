import json
import glob
import argparse
import re

topLevelCategoryMap = [
    # *1*/*A* = undergraduate course level constraint
    (re.compile('^\*([0-9A-Z])\*$'), lambda category: "[A-Z][A-Z][A-Z]{0}[0-9][0-9][HY]1".format(re.compile('^\*([0-9A-Z])\*$').match(category).group(1))),
    # CSC* = undergraduate department level constraint
    (re.compile('^([A-Z][A-Z][A-Z])\*$'), lambda category: "{0}[0-9][0-9][0-9][HY]1".format(re.compile('^([A-Z][A-Z][A-Z])\*$').match(category).group(1))),
    # CSC1* = undergraduate department and course level constraint
    (re.compile('^([A-Z][A-Z][A-Z][0-9A-Z])\*$'), lambda category: "{0}[0-9][0-9][HY]1".format(re.compile('^([A-Z][A-Z][A-Z][0-9A-Z])\*$').match(category).group(1))),
    # PHL* (GR) = graduate department level constraint
    (re.compile('^([A-Z][A-Z][A-Z])\* \(GR\)$'), lambda category: "{0}[0-9][0-9][0-9][0-9][HY]".format(re.compile('^([A-Z][A-Z][A-Z])\* \(GR\)$').match(category).group(1))),
    # * = Anything? TODO: figure out what this actually is
    (re.compile('^\*$'), lambda category: ".*"),
    # * (GR) = any graduate level course
    (re.compile('^\* \(GR\)$'), lambda category: "[A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9][HY]"),
    # CSC404H1 = specific undergraduate course code e.g. one of CSC404H1 or CSC236H1 or CSC324H1
    (re.compile('^[A-W][A-Z][A-Z][A-Z0-9][0-9][0-9][HY][0-9]$'), lambda category: "{0}".format(re.compile('^[A-Z][A-Z][A-Z][A-Z0-9][0-9][0-9][HY][0-9]$').match(category).group(0)))
]

def parseTopLevelCategory(category):
    for (regex, transform_func) in topLevelCategoryMap:
        if regex.match(category):
            return transform_func(category)
    return ""

def recursiveParseCourseCategory(courseCategory):
    # Open the file for this category and get the JSON
    ccFilename = "".join(i for i in courseCategory if i not in "\/:*?<>|")
    # complete_status - whether the regex is complete or now
    validatable = True


    try:
        with open(f"{args.cc_jsons_dir}/{ccFilename}.json") as f:
            categoryObj = json.load(f)
    except:
        validatable = False
        return ("", validatable)
        
    # Go through each include category and parse them into regexes
    includeRegexes = []
    for includeCategory in categoryObj["includeItems"]:
        categoryID = includeCategory["code"]
        if includeCategory["categoryEntity"]:
            # If it's another non-top-level id, recursively parse it again
            (regex, dependent_validatable) = recursiveParseCourseCategory(categoryID)
            validatable = validatable and dependent_validatable
            if dependent_validatable:
                includeRegexes.append(regex)
        else:
            # It's a base-level course category, parse it separately
            regex = parseTopLevelCategory(categoryID)
            # Complete if the string is not empty
            validatable = validatable and regex != ""
            if regex != "":
                includeRegexes.append(regex)

    # Do the same for the exclude category
    excludeRegexes = []
    for excludeCategory in categoryObj["excludeItems"]:
        categoryID = excludeCategory["code"]
        if excludeCategory["categoryEntity"]:
            (regex, dependent_validatable) = recursiveParseCourseCategory(categoryID)
            validatable = validatable and dependent_validatable
            if dependent_validatable:
                excludeRegexes.append(regex)
        else:
            regex = parseTopLevelCategory(categoryID)
            validatable = validatable and regex != ""
            if regex != "":
                excludeRegexes.append(regex)

    includeRegexString = f"({'|'.join(includeRegexes)})" if len(includeRegexes) != 0 else ""
    excludeRegexString = f"(?!{'|'.join(excludeRegexes)})" if len(excludeRegexes) != 0 else ""

    if includeRegexString == "":
        return (excludeRegexString, validatable)
    elif excludeRegexString == "":
        return (includeRegexString, validatable)
    else:
        return (f"({excludeRegexString}{includeRegexString})", validatable)


# Set up argument parsing and parse args
parser = argparse.ArgumentParser(description='Aggregates and parses course category JSON objects downloaded from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('--cc_jsons_dir', type=str, help="path to directory to read downloaded course category JSONs from. default: ./course_category_data", default="./course_category_data", metavar='dir')
parser.add_argument('--cc_ids_file', type=argparse.FileType('w'), help="path to file to write aggregated programs into. default: ./aggregated_course_categories.json", default="./aggregated_course_categories.json", metavar='file')

# Dict to hold final aggregated course categories obj
aggregated_course_categories = {}

# Start main
if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting course category aggregation...")

    attempted = 0

    for ccFile in glob.glob(f"{args.cc_jsons_dir}/*.json"):
        attempted += 1

        # Read file into dict
        with open(ccFile) as f:
            ccObj = json.load(f)
            courseCategory = ccObj["code"]

        (regex, complete_status) = recursiveParseCourseCategory(courseCategory)
        aggregated_course_categories[courseCategory] = {
            "regex": regex,
            "display": f"{courseCategory}: {ccObj['display']}".strip(),
            "validatable": complete_status
        }

    # We have finished modifying all the courses. Write aggregated_courses to file
    json.dump(aggregated_course_categories, args.cc_ids_file, ensure_ascii=False, separators=(',', ':'))

    # Print diagnostics
    print("Finished.")
    print(f"Cleaned and aggregated {attempted} course(s) from {args.cc_jsons_dir}")

    args.cc_ids_file.close()