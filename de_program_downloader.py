import requests
from pathlib import Path
import json
import fileinput
import sys
import re

from requests.api import head

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

# Set up argument parsing
parser = argparse.ArgumentParser(description='Downloads program JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('cookie', type=str, help="cookie from a valid Degree Explorer session. To obtain this, log into DE with your UofT credentials, then copy the cookie from the Network tab of Chrome Devtools")
parser.add_argument('--p_jsons_dir', type=str, help="path to directory to store downloaded program JSONs. default: ./program_data", default="./program_data", metavar='dir')

if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting program download...")

    # If a directory is indicated, created it if it doesn't exist
    if args.p_jsons_dir:
        Path(args.p_jsons_dir).mkdir(exist_ok=True, parents=True)

    # Load the cookies into the headers
    addProgramPOSTHeader["Cookie"] = args.cookie
    resetProgramsPOSTHeader["Cookie"] = args.cookie

    attempted = 0
    successes = 0
    skipped = []
    failures = []

    pRegex = re.compile('^AS(MAJ|SPE|MIN|FOC)([0-9]{4}).?$')
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
        for programDataObj in r.json()["timelineStatus"]["allPostAssessments"]:
            if programDataObj["postCode"] == programID:
                # Save the program info to file after extracting it from the morass
                with open(f"{args.p_jsons_dir}/{programID}.json", 'w') as f:
                    json.dump(programDataObj, f, ensure_ascii=False, indent=2)
                successes += 1
                break;

    # Reset the courses to clean up
    r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/resetPrograms?tabIndex=0", headers=resetProgramsPOSTHeader)

    # Print diagnostics
    print("Finished.")
    print(f"Attempted to download {attempted} program(s) from Degree Explorer:")
    print(f"\tSucceeded in downloading {successes} program(s)")
    print(f"\tSkipped {len(skipped)} program(s) because they have already been scraped. Skipped: {skipped}")
    print(f"\tFailed to download {len(failures)} program(s). Failed: {failures}")