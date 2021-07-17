#!/usr/bin/env python3

import json
import glob
import argparse
from pathlib import Path

# Set up argument parsing
parser = argparse.ArgumentParser(description='Downloads course JSON objects from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('--c_jsons_dir', type=str, help="path to directory to read downloaded course JSONs from. default: ./course_data", default="./course_data", metavar='dir')
parser.add_argument('--c_aggr_file', type=argparse.FileType('w'), help="path to file to write aggregated courses into. default: ./aggregated_courses.json", default="./aggregated_courses.json")

# Dict to hold final aggregated JSON obj
aggregated_courses = {}


if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting course aggregation...")

    attempted = 0

    for courseFile in glob.glob(f"{args.c_jsons_dir}/*.json"):
        attempted += 1

        # Read file into dict
        with open(courseFile) as f:
            courseObj = json.load(f)

        # From the top level, remove everything except these two
        for key in list(courseObj.keys()):
            if key != 'title' and key != 'prerequisites':
                del courseObj[key];

        # For each prerequisite, assemble the description and remove unwanted stuff. Assemble into a dict instead of a array, with the key being the shortIdentifer minus the brackets
        newPrereqs = {}
        for prereqObj in courseObj['prerequisites']:
            prereqID = prereqObj['shortIdentifier'][1:-1]

            # For each requisite item, we only need the code. The other information appears to be purely stylistic. We do this now since it makes it easier to create the prereqObj's display string
            for i in range(len(prereqObj['requisiteItems'])):
                prereqObj['requisiteItems'][i] = prereqObj['requisiteItems'][i]["code"]

            # Now, we proceed differently depending on whether the prereq is a 'NOTE' type of not. In both cases, the display string is added to a new attribute 'description'.
            keysToKeep = []
            if (prereqObj['type'] == 'NOTE'):
                # Create the string
                prereqObj["description"] = f"Note - {prereqObj['displaySuffix']}".strip();
                # Delete all other than these
                keysToKeep = ["type", "description"];
            else:
                listOfReqsStr = f" {prereqObj['subItemConnectorString']} ".join(prereqObj['requisiteItems'])
                prereqObj["description"] = f"{prereqObj['displayPrefix']} {listOfReqsStr} {prereqObj['displaySuffix']}".strip();
                keysToKeep = ["type", "count", "requisiteItems", "countType", "description"]

            for key in list(prereqObj.keys()):
                if key not in keysToKeep:
                    del prereqObj[key]

            # Done, add it to the new dict
            newPrereqs[prereqID] = prereqObj

        # Now that we have finished modifying everything, we add the new prereqs to the courseObj and append this to the final file
        courseObj['prerequisites'] = newPrereqs
        aggregated_courses[Path(courseFile).stem] = courseObj

    # We have finished modifying all the courses. Write aggregated_courses to file
    json.dump(aggregated_courses, args.c_aggr_file, ensure_ascii=False, indent=2)

    # Print diagnostics
    print("Finished.")
    print(f"Cleaned and aggregate {attempted} course(s) from {args.c_jsons_dir}")

    args.c_aggr_file.close()
