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
        ccFilename = "".join(i for i in courseCategory if i not in "\/:*?<>|")
        attempted += 1

        f = Path(f"{args.cc_jsons_dir}/{ccFilename}.json")
        if f.is_file():
            skipped.append(courseCategory)
            continue

        # Get the course category info. Yeah, it needs to be double encoded. Don't ask why.
        r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxStudent/getCategoryCourses?categoryCode={urllib.parse.quote(urllib.parse.quote(courseCategory))}", headers=getCategoryCourseGETHeader)
        if (r.status_code != 200):
            failures.append(courseCategory)
            continue

        with open(f"{args.cc_jsons_dir}/{ccFilename}.json", 'w') as f:
            json.dump(r.json(), f, ensure_ascii=False, indent=2)
        print(f"Downloaded data for {courseCategory}")
        successes += 1

    # Status info
    print("Finished.")
    print(f"Attempted to parse {attempted} course categories from stdin:")
    print(f"\tSucceeded in parsing {successes} categories")
    print(f"\tSkipped {len(skipped)} categories because they have already been parsed. Skipped: {skipped}")
    print(f"\tFailed to download {len(failures)} categories. Failed: {failures}")