#!/usr/bin/env python3

import requests
from pathlib import Path
import json
import argparse
import sys
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

# Set up argument parsing and parse args
parser = argparse.ArgumentParser(description='Downloads course category JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('cookie', type=str, help="cookie from a valid Degree Explorer session. To obtain this, log into DE with your UofT credentials, then copy the cookie from the Network tab of Chrome Devtools")
parser.add_argument('--cc_jsons_dir', type=str, help="path to directory to store downloaded course category JSONs. default: ./course_category_data", default="./course_category_data", metavar='dir')

def recursiveCourseCategoryDownload(categoryID):
    successes = 0
    skipped = []
    failures = []

    # Check if it's already been downloaded.
    ccFilename = "".join(i for i in categoryID if i not in "\/:*?<>|")
    f = Path(f"{args.cc_jsons_dir}/{ccFilename}.json")

    # If it has not, download it
    if not f.is_file():
        # Download it if not. Yeah, it needs to be double encoded. Don't ask why.
        r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxStudent/getCategoryCourses?categoryCode={urllib.parse.quote(urllib.parse.quote(categoryID))}", headers=getCategoryCourseGETHeader)
        if (r.status_code != 200):
            # Chalk this up as a failure, and return with 0 successes and skips
            failures += [categoryID]
            return (successes, skipped, failures)
        categoryObj = r.json()

        # Save the json to file
        with open(f"{args.cc_jsons_dir}/{ccFilename}.json", 'w') as f:
            json.dump(categoryObj, f, ensure_ascii=False, indent=2)
        # Getting this succeeded
        successes += 1
    # If it has, open it and get the object
    else:
        with open(f"{args.cc_jsons_dir}/{ccFilename}.json", 'r') as f:
            categoryObj = json.load(f)
        # This was skipped since it's already been downloaded before
        skipped += [categoryID]


    # Check includes for dependent categories
    for includeCategory in categoryObj["includeItems"]:
        # If it's marked as a category, try to download it as well. Otherwise, leave it
        if includeCategory["categoryEntity"]:
            (sucs, skips, fails) = recursiveCourseCategoryDownload(includeCategory["code"])
            # Add to here how many of the include categories succeeded, were skipped, or failed
            successes += sucs
            skipped += skips
            failures += fails
    # Do the same for the exclude categories
    for excludeCategory in categoryObj["excludeItems"]:
        # If it's marked as a category, try to download it as well. Otherwise, leave it
        if excludeCategory["categoryEntity"]:
            (sucs, skips, fails) = recursiveCourseCategoryDownload(excludeCategory["code"])
            successes += sucs
            skipped += skips
            failures += fails

    return (successes, skipped, failures)


# Start main
if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting course category download...")

    # If a directory is indicated, created it if it doesn't exist
    if args.cc_jsons_dir:
        Path(args.cc_jsons_dir).mkdir(exist_ok=True, parents=True)

    # Load the cookies into the headers
    getCategoryCourseGETHeader["Cookie"] = args.cookie

    # Status vars for the program
    attempted = 0
    successes = 0
    skipped = []
    failures = []

    for line in sys.stdin:
        courseCategory = line.strip()
        attempted += 1

        (sucs, skips, fails) = recursiveCourseCategoryDownload(courseCategory)
        successes += sucs
        skipped += skips
        failures += fails

        print(f"{courseCategory} - Successes:{sucs}, Skips:{len(skips)}, Fails:{len(fails)}")

    # Status info
    print("Finished.")
    print(f"Attempted to parse {attempted} course categories from stdin:")
    print(f"\tSucceeded in parsing {successes} categories, both from stdin and their unlisted dependent categories")
    print(f"\tSkipped {len(set(skipped))} categories because they have already been parsed. Skipped: {set(skipped)}")
    print(f"\tFailed to download {len(set(failures))} categories. Failed: {set(failures)}")