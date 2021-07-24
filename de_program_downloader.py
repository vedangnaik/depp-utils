import requests
from pathlib import Path
import json
import argparse
import sys
import re
import urllib

import pprint

addProgramPOSTHeader = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Length": "0",
    "Content-Type": "text/plain",
    "DNT": "1",
    "Host": "degreeexplorer.utoronto.ca",
    "Origin": "https://degreeexplorer.utoronto.ca",
    "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "X-XSRF-TOKEN": "Vcs464vTo6UCHRjbIlLx8rMMBd8V8NIxVkLGnZGA5lU=",
    "Cookie": ""
}

resetProgramsPOSTHeader = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Content-Length": "0",
    "Content-Type": "text/plain",
    "DNT": "1",
    "Host": "degreeexplorer.utoronto.ca",
    "Origin": "https://degreeexplorer.utoronto.ca",
    "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
    "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
    "sec-ch-ua-mobile": "?0",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "X-XSRF-TOKEN": "vtV17/yE+Sq6deyRxCWe1LFZCvUx1GE2+n00MwPDLcw=",
    "Cookie": ""
}

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

# Set up argument parsing
parser = argparse.ArgumentParser(description='Downloads program JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('cookie', type=str, help="cookie from a valid Degree Explorer session. To obtain this, log into DE with your UofT credentials, then copy the cookie from the Network tab of Chrome Devtools")
parser.add_argument('--p_jsons_dir', type=str, help="path to directory to store downloaded program JSONs. default: ./program_data", default="./program_data", metavar='dir')
parser.add_argument('--cg_jsons_dir', type=str, help="path to directory to store downloaded course group JSONs. default: ./course_groups_data", default="./course_groups_data", metavar='dir')

def recursiveDownloadCourseCategory(courseCategory):
    r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxStudent/getCategoryCourses?categoryCode={urllib.parse.quote(urllib.parse.quote(courseCategory))}", headers=getCategoryCourseGETHeader)
    if (r.status_code != 200):
        print(f"{urllib.parse.quote(urllib.parse.quote(courseCategory))} get failed, returning...")
        return "";
    
    # Save here instead
    categoryObj = r.json()
    # pprint.pprint(categoryObj)

    includes = []
    for includeCategory in categoryObj["includeItems"]:
        if includeCategory["categoryEntity"]:
            includes.append(recursiveDownloadCourseCategory(includeCategory["code"]))
        else:
            includes.append(includeCategory["code"])

    excludes = []
    for excludeCategory in categoryObj["excludeItems"]:
        if excludeCategory["categoryEntity"]:
            excludes.append(recursiveDownloadCourseCategory(excludeCategory["code"]))
        else:
            excludes.append(excludeCategory["code"])

    includes = f"({'|'.join(includes)})" if len(includes) != 0 else ""
    excludes = f"(?!{'|'.join(excludes)})" if len(excludes) != 0 else ""

    if includes == "":
        return excludes
    elif excludes == "":
        return includes
    else:
        return f"({excludes}{includes})"



if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting program download...")

    # If a directory is indicated, created it if it doesn't exist
    if args.p_jsons_dir:
        Path(args.p_jsons_dir).mkdir(exist_ok=True, parents=True)

    # Load the cookies into the headers
    addProgramPOSTHeader["Cookie"] = args.cookie
    resetProgramsPOSTHeader["Cookie"] = args.cookie
    getCategoryCourseGETHeader["Cookie"] = args.cookie

    print(recursiveDownloadCourseCategory("CSC_INTEGRATIVE_20215"))
    sys.exit(0)

    attempted = 0
    successes = 0
    skipped = []
    failures = []

    cRegex = re.compile('^[A-Z]{3}[1-4][0-9]{2}[HY][01]$')
    pRegex = re.compile('^AS(MAJ|SPE|MIN|FOC)([0-9]{4}).?$')
    reqRegex = re.compile('^Req[0-9]{1,3}$')
    currentStudyArea = None

    for line in sys.stdin:
        programID = line.strip()
        studyAreaNum = pRegex.match(programID).group(2)
        attempted += 1

        # Skip the program if we've already scraped it
        f = Path(f"{args.p_jsons_dir}/{programID}.json")
        if f.is_file():
            skipped.append(programID)
            continue

        # Reset if we've finished all the programs from this subject area
        if (studyAreaNum != currentStudyArea):
            r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/resetPrograms?tabIndex=0", headers=resetProgramsPOSTHeader)
            if (r.status_code != 200):
                print("Course reset failed, quitting for now...")
                sys.exit(1)
            print(f"Reseting programs for number {currentStudyArea}, moving to {studyAreaNum}")
            currentStudyArea = studyAreaNum

        # Add the program, hopefully it doesn't fail due to an un-added prereq program
        r = requests.post(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveProgramEntry?tabIndex=0&newPostCode={programID}", headers=addProgramPOSTHeader)
        if (r.status_code != 200):
            failures.append(programID)
            continue


        # Go through each program obj to only extract the one we added. 
        # Yeah, don't ask why it's this way.
        thisProgramObj = list(filter(lambda programDataObj: programDataObj["postCode"] == programID, r.json()["timelineStatus"]["allPostAssessments"]))[0]

        # Save the program info to file after extracting it from the morass
        # with open(f"{args.p_jsons_dir}/{programID}.json", 'w', encoding='utf-8') as f:
        #     json.dump(thisProgramObj, f, ensure_ascii=False, indent=2)     
                   
        # Now, we need to go through every course this program references, and download any of those strange course group things
        courseCategories = []
        for detailAssessment in thisProgramObj["detailAssessments"]:
            for requisiteItem in detailAssessment["requirement"]["requisiteItems"]:
                code = requisiteItem["code"]
                if not cRegex.match(code) and not reqRegex.match(code):
                    courseCategories.append(code)

        print(courseCategories)
        for courseCategory in courseCategories:
            # recursiveDownloadCourseCategory(courseCategory)
            print()

        successes += 1 

    # Reset the courses to clean up
    r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/resetPrograms?tabIndex=0", headers=resetProgramsPOSTHeader)

    # Print diagnostics
    print("Finished.")
    print(f"Attempted to download {attempted} program(s) from Degree Explorer:")
    print(f"\tSucceeded in downloading {successes} program(s)")
    print(f"\tSkipped {len(skipped)} program(s) because they have already been scraped. Skipped: {skipped}")
    print(f"\tFailed to download {len(failures)} program(s). Failed: {failures}")