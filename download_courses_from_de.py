import requests
from pathlib import Path
import json
import fileinput
import sys

courseInfoGETHeader = {
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
    "Cookie": "" # Passed in by user for that session
}

courseAddPOSTHeader = {
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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python download_courses_from_de.py rowNum colNum cookie")
        print("Pass in course IDs via stdin.")

    courseAddPOSTHeader["Cookie"] = sys.argv[3]
    courseInfoGETHeader["Cookie"] = sys.argv[3]

    attempted = 0
    skipped = []
    successes = 0
    failures = []

    for line in sys.stdin:
        courseID = line.strip()
        attempted += 1

        f = Path("course_data/" + courseID + ".json")
        if f.is_file():
            skipped.append(courseID)
            continue

        r = requests.post(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveCourseEntry?tabIndex=1&selRowIndex={sys.argv[1]}&selColIndex={sys.argv[2]}&newCourseCode={courseID}", headers=courseAddPOSTHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            continue
        
        r = requests.get(f"https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/getCellDetails?tabIndex=1&rowIndex={sys.argv[1]}&colIndex={sys.argv[2]}", headers=courseInfoGETHeader)
        if (r.status_code != 200):
            failures.append(courseID)
            continue

        with open("course_data/" + courseID + ".json", 'w', encoding='utf-8') as f:
            json.dump(r.json(), f, ensure_ascii=False, indent=2)
        print(f"Downloaded data for {courseID}")
        successes += 1

    print(f"Attempted to download {attempted} courses from DE as passed in via stdin.")
    print(f"Succeeded in downloading {successes} courses.")
    print(f"Skipped {len(skipped)} courses because they have already been scraped.")
    print(f"Failed to download {len(failures)} courses. Failed courses: ")
    print(failures)





# programInfoPOSTHeader = {
#     "Accept": "application/json, text/plain, */*",
#     "Accept-Encoding": "gzip, deflate, br",
#     "Accept-Language": "en-US,en;q=0.9",
#     "Connection": "keep-alive",
#     "Content-Length": "0",
#     "Content-Type": "text/plain",
#     "DNT": "1",
#     "Host": "degreeexplorer.utoronto.ca",
#     "Origin": "https://degreeexplorer.utoronto.ca",
#     "Referer": "https://degreeexplorer.utoronto.ca/degreeExplorer/planner",
#     "sec-ch-ua": '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
#     "sec-ch-ua-mobile": "?0",
#     "Sec-Fetch-Dest": "empty",
#     "Sec-Fetch-Mode": "cors",
#     "Sec-Fetch-Site": "same-origin",
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#     "X-XSRF-TOKEN": "Vcs464vTo6UCHRjbIlLx8rMMBd8V8NIxVkLGnZGA5lU=",
#     "Cookie": ""
# }

# programInfoPOSTHeader["Cookie"] = cookie

# for programID in programs:
#     r = requests.post("https://degreeexplorer.utoronto.ca/degreeExplorer/rest/dxPlanner/saveProgramEntry?tabIndex=0&newPostCode=" + programID, headers=programInfoPOSTHeader)
#     if (r.status_code != 200):
#         print("Failed")
#     print(r.text)