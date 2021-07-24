import requests
import json
import argparse
import sys
import re
import urllib

getCategoryCourseGETHeader = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Cookie": "",
    "DNT": "1",
    "Host": "degreeexplorer.utoronto.ca",
    "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
    "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
}

# *1*/*A* = course level constraint
# * (blah blah) = specific categoies like graduate, transfer, etc.
# CSC* = department level constraint
# CSC1 = department+course level constraint
def parseTopLevelCategory(category):
    courseLevelRegex = re.compile('^\*([0-9A-Z])\*$')
    categoryRegex = re.compile('^\* \(.*\)$')
    departmentLevelRegex = re.compile('^([A-Z]{3})\*$')
    departmentAndCourseRegex = re.compile('^([A-Z]{3}[0-9A-Z])\*$')

    if courseLevelRegex.match(category):
        return f"[A-Z]{{3}}{courseLevelRegex.match(category).group(1)}[0-9]{{2}}[HY]1"
    elif categoryRegex.match(category):
        return "^\\b$";
    elif departmentLevelRegex.match(category):
        return f"{departmentLevelRegex.match(category).group(1)}[0-9]{{3}}[HY]1"
    elif departmentAndCourseRegex.match(category):
        return f"{departmentAndCourseRegex.match(category).group(1)}[0-9]{2}[HY]1"
    else:
        print(f"Unknown top-level type {category}")
        return ""

def recursiveParseCourseCategory(courseCategory):
    # Yeah, this courseID needs to be double encoded for some reason. Don't ask.
    r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxStudent/getCategoryCourses?categoryCode={urllib.parse.quote(urllib.parse.quote(courseCategory))}", headers=getCategoryCourseGETHeader)
    if (r.status_code != 200):
        print(f"{urllib.parse.quote(urllib.parse.quote(courseCategory))} get failed, returning...")
        # This is a special regex which does not match any string ;)
        return "^\b$";
    
    # Save here instead
    categoryObj = r.json()
    # pprint.pprint(categoryObj)

    includes = []
    for includeCategory in categoryObj["includeItems"]:
        categoryID = includeCategory["code"]
        if includeCategory["categoryEntity"]:
            # If it's another non-top-level id, recursively parse it again
            includes.append(recursiveParseCourseCategory(categoryID))
        elif includeCategory["courseEntity"]:
            # Pass the course ID through, it's the exact regex we need
            includes.append(categoryID)
        else:
            # Start parsing out these various base-level course categories
            includes.append(parseTopLevelCategory(categoryID))

    excludes = []
    for excludeCategory in categoryObj["excludeItems"]:
        categoryID = excludeCategory["code"]
        if excludeCategory["categoryEntity"]:
            # If it's another non-top-level id, recursively parse it again
            excludes.append(recursiveParseCourseCategory(categoryID))
        elif excludeCategory["courseEntity"]:
            # Pass the course ID through, it's the exact regex we need
            excludes.append(categoryID)
        else:
            # Start parsing out these various base-level course categories
            excludes.append(parseTopLevelCategory(categoryID))

    includes = f"({'|'.join(includes)})" if len(includes) != 0 else ""
    excludes = f"(?!{'|'.join(excludes)})" if len(excludes) != 0 else ""

    if includes == "":
        return excludes
    elif excludes == "":
        return includes
    else:
        return f"({excludes}{includes})"


# Set up argument parsing and parse args
parser = argparse.ArgumentParser(description='Downloads program JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('cookie', type=str, help="cookie from a valid Degree Explorer session. To obtain this, log into DE with your UofT credentials, then copy the cookie from the Network tab of Chrome Devtools")
parser.add_argument('--cc_ids_file', type=argparse.FileType('a+'), help="path to ASCII file to store parsed course category regexs. default: ./course-category-data.txt", default="./course-category-data.txt", metavar='file')

# Start main
if __name__ == "__main__":
    args = parser.parse_args()
    
    print("Starting course category parsing...")

    # Load the cookies into the headers
    getCategoryCourseGETHeader["Cookie"] = args.cookie

    # Status vars for the program
    attempted = 0
    successes = 0
    skipped = []
    failures = []

    # Dict to hold all regexes seen so far, and to write into file
    args.cc_ids_file.seek(0)
    ccRegexs = [line.split(":")[0].strip() for line in args.cc_ids_file.readlines()]

    for line in sys.stdin:
        category = line.strip()
        if category in ccRegexs:
            skipped.append(category)
        else:
            args.cc_ids_file.write(f"{category}: {recursiveParseCourseCategory(category)}\n")
            ccRegexs.append(category)
            successes += 1
        attempted += 1

    # Status info
    print("Finished.")
    print(f"Attempted to parse {attempted} course categories from stdin:")
    print(f"\tSucceeded in parsing {successes} categories")
    print(f"\tSkipped {len(skipped)} categories because they have already been parsed. Skipped: {skipped}")
    print(f"\tFailed to download {len(failures)} categories. Failed: {failures}")

    # Close stuff
    args.cc_ids_file.close()