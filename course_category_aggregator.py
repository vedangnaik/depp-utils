import json
import glob
import argparse
import re

topLevelCategoryMap = [
    # *1*/*A* = undergraduate course level constraint
    (re.compile('^\*([0-9A-Z])\*$'), lambda category: "[A-Z]{{3}}{0}[0-9]{{2}}[HY]1".format(re.compile('^\*([0-9A-Z])\*$').match(category).group(1))),
    # CSC* = undergraduate department level constraint
    (re.compile('^([A-Z]{3})\*$'), lambda category: "{0}[0-9]{{3}}[HY]1".format(re.compile('^([A-Z]{3})\*$').match(category).group(1))),
    # CSC1* = undergraduate department and course level constraint
    (re.compile('^([A-Z]{3}[0-9A-Z])\*$'), lambda category: "{0}[0-9]{{2}}[HY]1".format(re.compile('^([A-Z]{3}[0-9A-Z])\*$').match(category).group(1))),
    # PHL* (GR) = graduate department level constraint
    (re.compile('^([A-Z]{3})\* \(GR\)$'), lambda category: "{0}[0-9]{{4}}[HY]".format(re.compile('^([A-Z]{3})\* \(GR\)$').match(category).group(1))),
    # * = Anything? TODO: figure out what this actually is
    (re.compile('^\*$'), lambda category: ".*"),
    # * (GR) = any graduate level course
    (re.compile('^\* \(GR\)$'), lambda category: "[A-Z]{{3}}[0-9]{{4}}[HY]"),
    # CSC404H1 = specific undergraduate course code e.g. one of CSC404H1 or CSC236H1 or CSC324H1
    (re.compile('^([A-Z]{3}[0-9]{3}[HY]1$)'), lambda category: "{0}".format(re.compile('^([A-Z]{3}[0-9]{3}[HY]1$)').match(category).group(1)))
]

def parseTopLevelCategory(category):
    for (regex, transform_func) in topLevelCategoryMap:
        if regex.match(category):
            return transform_func(category)
        else:
            return ""

def recursiveParseCourseCategory(courseCategory):
    # Open the file for this category and get the JSON
    ccFilename = "".join(i for i in courseCategory if i not in "\/:*?<>|")
    with open(f"{args.cc_jsons_dir}/{ccFilename}.json") as f:
        categoryObj = json.load(f)
        
    # Go through each include category and parse them into regexes
    includeRegexes = []
    for includeCategory in categoryObj["includeItems"]:
        categoryID = includeCategory["code"]
        if includeCategory["categoryEntity"]:
            # If it's another non-top-level id, recursively parse it again
            includeRegexes.append(recursiveParseCourseCategory(categoryID))
        elif includeCategory["courseEntity"]:
            # Pass the course ID through, it's the exact regex we need
            includeRegexes.append(categoryID)
        else:
            # Start parsing out these various base-level course categories
            includeRegexes.append(parseTopLevelCategory(categoryID))

    # Do the same for the exclude category
    excludeRegexes = []
    for excludeCategory in categoryObj["excludeItems"]:
        categoryID = excludeCategory["code"]
        if excludeCategory["categoryEntity"]:
            excludeRegexes.append(recursiveParseCourseCategory(categoryID))
        elif excludeCategory["courseEntity"]:
            excludeRegexes.append(categoryID)
        else:
            excludeRegexes.append(parseTopLevelCategory(categoryID))

    includeRegexString = f"({'|'.join(includeRegexes)})" if len(includeRegexes) != 0 else ""
    excludeRegexString = f"(?!{'|'.join(excludeRegexes)})" if len(excludeRegexes) != 0 else ""

    if includeRegexString == "":
        return excludeRegexString
    elif excludeRegexString == "":
        return includeRegexString
    else:
        return f"({excludeRegexString}{includeRegexString})"


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

        print(ccFile)
        aggregated_course_categories[courseCategory] = recursiveParseCourseCategory(courseCategory)

    # We have finished modifying all the courses. Write aggregated_courses to file
    print(aggregated_course_categories)
    json.dump(aggregated_course_categories, args.cc_ids_file, ensure_ascii=False, indent=2)

    # Print diagnostics
    print("Finished.")
    print(f"Cleaned and aggregate {attempted} course(s) from {args.cc_jsons_dir}")

    args.cc_ids_file.close()