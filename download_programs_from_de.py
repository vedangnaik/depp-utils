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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python download_programs_from_de.py cookie")
        print("Pass in program IDs via stdin.")
        sys.exit(1);

    addProgramPOSTHeader["Cookie"] = sys.argv[1]
    resetProgramsPOSTHeader["Cookie"] = sys.argv[1]

    attempted = 0
    skipped = []
    successes = 0
    failures = []

    pRegex = re.compile('^AS(MAJ|SPE|MIN|FOC)([0-9]{4}).?$')
    currentStudyArea = None

    for line in sys.stdin:
        programID = line.strip()
        studyAreaNum = pRegex.match(programID).group(2)
        attempted += 1

        # Skip the program if we've already scraped it
        f = Path("program_data/" + programID + ".json")
        if f.is_file():
            skipped.append(programID)
            continue

        # We are not, reset the courses
        if (studyAreaNum != currentStudyArea):
            r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/resetPrograms?tabIndex=0", headers=resetProgramsPOSTHeader)
            if (r.status_code != 200):
                print("Course reset failed, quitting for now...")
                sys.exit(1)
            print(f"Reseting programs for number {currentStudyArea}, moving to {studyAreaNum}")
            currentStudyArea = studyAreaNum

        # Add the course, hopefully it doesn't fail due to an un-added prereq program
        r = requests.post(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveProgramEntry?tabIndex=0&newPostCode={programID}", headers=addProgramPOSTHeader)
        if (r.status_code != 200):
            failures.append(programID)
            continue

        # Go through each program obj to only extract the one we added. Yeah, don't ask why it's this way.
        for programDataObj in r.json()["timelineStatus"]["allPostAssessments"]:
            if programDataObj["postCode"] == programID:
                # Save the program info to file after extracting it from the morass
                with open("program_data/" + programID + ".json", 'w', encoding='utf-8') as f:
                    json.dump(programDataObj, f, ensure_ascii=False, indent=2)
                successes += 1   
                break;

    # Reset the courses to clean up
    r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/resetPrograms?tabIndex=0", headers=resetProgramsPOSTHeader)

    print(f"Attempted to download {attempted} courses from DE as passed in via stdin.")
    print(f"Succeeded in downloading {successes} courses.")
    print(f"Skipped {len(skipped)} courses because they have already been scraped.")
    print(f"Failed to download {len(failures)} courses. Failed courses: ")
    print(failures)

    sys.exit(0);
