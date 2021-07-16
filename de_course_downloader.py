#!/usr/bin/env python3

import requests
from pathlib import Path
import json
import argparse
import sys

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
parser.add_argument('--c_jsons_dir', type=str, help="path to directory to store downloaded course JSONs", default="./course_data", metavar='dir')


if __name__ == "__main__":
    args = parser.parse_args()

    # If a directory is indicated, created it if it doesn't exist
    if args.c_jsons_dir:
        Path(args.c_jsons_dir).mkdir(exist_ok=True, parents=True)

    # Load the cookies into the headers
    addCoursePOSTHeader["Cookie"] = args.cookie
    getCourseInfoGETHeader["Cookie"] = args.cookie

    attempted = 0
    successes = 0
    skipped = []
    failures = []

    for line in sys.stdin:
        courseID = line.strip()
        attempted += 1

        f = Path(f"{args.c_jsons_dir}/{courseID}.json")
        if f.is_file():
            skipped.append(courseID)
            continue

        # Add the course, then get it's info. Equivalent to adding it by hovering+typing, then seeing the information by clicking on the tile.
        r = requests.post(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveCourseEntry?tabIndex=1&selRowIndex={args.row_num}&selColIndex={args.col_num}&newCourseCode={courseID}", headers=addCoursePOSTHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            continue
        
        r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/getCellDetails?tabIndex=1&rowIndex={args.row_num}&colIndex={args.col_num}", headers=getCourseInfoGETHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            continue

        with open(f"{args.c_jsons_dir}/{courseID}.json", 'w') as f:
            json.dump(r.json(), f, ensure_ascii=False, indent=2)
        print(f"Downloaded data for {courseID}")
        successes += 1

    # Print diagnostics
    print("Finished.")
    print(f"Attempted to download {attempted} courses from Degree Explorer:")
    print(f"\tSucceeded in downloading {successes} courses")
    print(f"\tSkipped {len(skipped)} courses because they have already been scraped. Skipped courses: {skipped}")
    print(f"\tFailed to download {len(failures)} courses. Failed courses: {failures}")