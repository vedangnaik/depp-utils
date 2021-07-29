#!/usr/bin/env python3

import requests
from pathlib import Path
import json
import argparse
import sys
import re

getCourseInfoGETHeader = {
    "Host": "degreeexplorer.utoronto.ca",
    "Connection": "keep-alive",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "Accept": "application/json, text/plain, */*",
    "DNT": "1",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": ""
}

addCoursePOSTHeader = {
    "Host": "degreeexplorer.utoronto.ca",
    "Connection": "keep-alive",
    "Content-Length": "0",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "Accept": "application/json, text/plain, */*",
    "DNT": "1",
    "X-XSRF-TOKEN": "eYH6RC3MRwtk1RJfFsMbjTt1KBpsAcDC7wuTvHMJ+Uw=",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Content-Type": "text/plain",
    "Origin": "https://degreeexplorer.utoronto.ca",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": ""
}

# Set up argument parsing
parser = argparse.ArgumentParser(description='Downloads course JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('cookie', type=str, help="cookie from a valid Degree Explorer session. To obtain this, log into DE with your UofT credentials, then copy the cookie from the Network tab of Chrome Devtools")
parser.add_argument('row_num', type=int, help="row num of DE timetable into which to add courses before download")
parser.add_argument('col_num', type=int, help="col num of DE timetable into which to add courses before download")
parser.add_argument('--c_jsons_dir', type=str, help="path to directory to store downloaded course JSONs. default: ./course_data", default="./course_data", metavar='dir')
parser.add_argument('--c_cc_ids_file', type=argparse.FileType('a'), help="path to ASCII file to store course categories from downloaded course JSONs. default: ./courses-course-category-ids.txt", default="./courses-course-category-ids.txt", metavar='file')

if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting course download...")

    # If a directory is indicated, created it if it doesn't exist
    if args.c_jsons_dir:
        Path(args.c_jsons_dir).mkdir(exist_ok=True, parents=True)

    # Load the cookies into the headers
    addCoursePOSTHeader["Cookie"] = args.cookie
    getCourseInfoGETHeader["Cookie"] = args.cookie

    # Status vars
    attempted = 0
    successes = 0
    skipped = []
    failures = []
    # Used to keep track of how many have failed in a row. If it's more than a threshold, the cookie has likely become invalid. Auto-quit at that point to stop hammering the server.
    consecutive_failures = 0

    # Regexs used for course, program, and requirement identification
    cRegex = re.compile('^[A-Z]{3}[A-Z0-9][0-9]{2,3}[HY][0-9]?$')
    pRegex = re.compile('^AS(MAJ|SPE|MIN|FOC)([0-9]{4}).?$')
    prereqRegex = re.compile('^P[0-9]{1,3}$')

    for line in sys.stdin:
        if consecutive_failures >= 20:
            print(f"Detected {consecutive_failures} consecutive failures. This is likely because the cookie has become invalid. Quitting now to avoid unnecessary API calls.")
            break

        courseID = line.strip()
        attempted += 1

        # Skip the course if we've already scraped it
        f = Path(f"{args.c_jsons_dir}/{courseID}.json")
        if f.is_file():
            skipped.append(courseID)
            continue

        # Add the course, then get it's info. Equivalent to adding it by hovering+typing, then seeing the information by clicking on the tile.
        r = requests.post(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveCourseEntry?tabIndex=1&selRowIndex={args.row_num}&selColIndex={args.col_num}&newCourseCode={courseID}", headers=addCoursePOSTHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            consecutive_failures += 1
            continue
        r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/getCellDetails?tabIndex=1&rowIndex={args.row_num}&colIndex={args.col_num}", headers=getCourseInfoGETHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            consecutive_failures += 1
            continue
        thisCourseObj = r.json()

        # Save the program info to file
        with open(f"{args.c_jsons_dir}/{courseID}.json", 'w') as f:
            json.dump(thisCourseObj, f, ensure_ascii=False, indent=2)

        # Save any course categories from this one's exclusions, corequisites, and prerequisites
        for category in ["prerequisites", "corequisites", "orderedExclusions"]:
            for categoryObj in thisCourseObj[category]:
                for requisiteItem in categoryObj["requisiteItems"]:
                    code = requisiteItem["code"]
                    if not cRegex.match(code) and not pRegex.match(code) and not prereqRegex.match(code) and code != "":
                        args.c_cc_ids_file.write(code + "\n")

        print(f"Downloaded data for {courseID}")
        consecutive_failures = 0 # Reset this
        successes += 1

    # Print diagnostics
    print("Finished.")
    print(f"Attempted to download {attempted} course(s) from Degree Explorer:")
    print(f"\tSucceeded in downloading {successes} course(s)")
    print(f"\tSkipped {len(skipped)} course(s) because they have already been scraped. Skipped: {skipped}")
    print(f"\tFailed to download {len(failures)} course(s). Failures: {failures}")