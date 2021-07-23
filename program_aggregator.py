#!/usr/bin/env python3

import json
import glob
import argparse
from pathlib import Path

# Set up argument parsing
parser = argparse.ArgumentParser(description='Aggregates and cleans program JSON objects downloaded from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('--p_jsons_dir', type=str, help="path to directory to read downloaded program JSONs from. default: ./program_data", default="./program_data", metavar='dir')
parser.add_argument('--p_aggr_file', type=argparse.FileType('w'), help="path to file to write aggregated programs into. default: ./aggregated_programs.json", default="./aggregated_programs.json", metavar='file')

# Dict to hold final aggregated JSON obj
aggregated_programs = {}


if __name__ == "__main__":
    args = parser.parse_args()

    print("Starting program aggregation...")

    attempted = 0

    for programFile in glob.glob(f"{args.p_jsons_dir}/*.json"):
        attempted += 1

        # Read file into dict
        with open(programFile) as f:
            programObj = json.load(f)

        # From the top level, remove everything except these two
        for key in list(programObj.keys()):
            if key not in ["title", "detailAssessments"]:
                del programObj[key];

        # For each requirement, first bring the embedded requirement object a level higher and make it a dict instead of a list
        newPrereqs = {}
        for reqObj in programObj['detailAssessments']:
            reqID = reqObj['shortIdentifier'][1:-1]
            reqObj['requirement']['count'] = reqObj['credits']['requiredCredits']
            newPrereqs[reqID] = reqObj['requirement']
        programObj['detailAssessments'] = newPrereqs

        # Keep only the code for each requisite item. This will make it easier to assemble the description later
        for _, reqObj in programObj['detailAssessments'].items():
            for i in range(len(reqObj['requisiteItems'])):
                reqObj['requisiteItems'][i] = reqObj['requisiteItems'][i]["code"]

        # Now, we go through each requirement and clean it. We all add a nicer description
        keysToKeep = []
        for _, reqObj in programObj['detailAssessments'].items():
            if reqObj['type'] == 'NOTE':
                reqObj['description'] = reqObj['displayPrefix']
                keysToKeep = ['type', 'description']
            else:
                listOfReqsStr = f" {reqObj['subItemConnectorString']} ".join(reqObj['requisiteItems'])
                reqObj["description"] = f"{reqObj['displayPrefix']} {listOfReqsStr} {reqObj['displaySuffix']}".strip();
                keysToKeep = ["type", "count", "requisiteItems", "description"]
        
            # Remove unwanted keys
            for key in list(reqObj.keys()):
                if key not in keysToKeep:
                    del reqObj[key]           

        # Now that we have finished modifying everything, we add the new prereqs to the courseObj and append this to the final file
        aggregated_programs[Path(programFile).stem] = programObj

    # We have finished modifying all the courses. Write aggregated_courses to file
    json.dump(aggregated_programs, args.p_aggr_file, ensure_ascii=False, indent=2)

    # Print diagnostics
    print("Finished.")
    print(f"Cleaned and aggregate {attempted} course(s) from {args.p_jsons_dir}")

    args.p_aggr_file.close()
