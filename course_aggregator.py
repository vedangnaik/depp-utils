#!/usr/bin/env python3

import json
import glob
import argparse
from pathlib import Path

from constants import allCoursesRe, allProgramsRe, prerequisiteRe

# Set up argument parsing
parser = argparse.ArgumentParser(description='Aggregates and cleans course JSON objects downloaded from https://degreeexplorer.utoronto.ca/.')
parser.add_argument('--c_jsons_dir', type=str, help="path to directory to read downloaded course JSONs from. default: ./course_data", default="./course_data", metavar='dir')
parser.add_argument('--c_aggr_file', type=argparse.FileType('w'), help="path to file to write aggregated courses into. default: ./aggregated_courses.json", default="./aggregated_courses.json", metavar='file')

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
            if key not in ['title', 'prerequisites']:
                del courseObj[key];

        # For each prerequisite, assemble the description and remove unwanted stuff. Assemble into a dict instead of a array, with the key being the shortIdentifer minus the brackets
        newPrereqs = {}
        for prereqObj in courseObj['prerequisites']:
            prereqID = prereqObj['shortIdentifier'][1:-1]

            displayPrefix = prereqObj["displayPrefix"]
            connector = prereqObj['subItemConnectorString']
            displaySuffix = prereqObj["displaySuffix"]
            # We need the actual codes to make the display string
            requisiteCodes = []
            # For ease of use
            type_ = prereqObj["type"]
            countType = prereqObj["countType"]

            # For each requisite item, we only need the code and the type of the code i.e. course, program, or category, or another prereq. We will group them via these labels.
            courses = []
            programs = []
            categories = []
            dependentPrereqs = []
            for i in range(len(prereqObj['requisiteItems'])):
                code = prereqObj['requisiteItems'][i]["code"]
                requisiteCodes.append(code)
                if allCoursesRe.match(code):
                    courses.append(code)
                elif allProgramsRe.match(code):
                    programs.append(code)
                elif prerequisiteRe.match(code):
                    dependentPrereqs.append(code)
                else:
                    categories.append(code)
            
            # Now, we proceed differently depending on what types and countTypes and other factors this prerequisite has. Reduction in final file size can be acheived by determining ahead of time which requisites are unverifiable, and reducing their content.
            # Array of prereq obj keys to keep. Can be modified as necessary to include the bare minimum needed, but these two are mandatory for all.
            keysToKeep = ["description", "type"]
            # We will combine all of these subtypes into a single 'unverifiable' type to save space.
            if countType in ["AVERAGE", "YOS", "GPA", "GRADE"] or type_ == "COMPLEX":
                prereqObj["type"] = "UNVERIFIABLE"
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
            # These types are all verifiable, but we can still do some more preprocessing to save space. This includes removing unwanted stuff and combining countTypes and types into a single field
            else:
                if type_ == "NOTE":
                    prereqObj["description"] = displaySuffix.strip()

                # REQUISITES family - only one relevant type
                elif countType == "REQUISITES" and type_ == "MINIMUM":
                    keysToKeep += ["count", "dependentPrereqs"]

                    prereqObj["type"] = "REQUISITES_MIN"
                    listOfReqsStr = f" {connector} ".join(requisiteCodes)
                    prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                    prereqObj["dependentPrereqs"] = dependentPrereqs

                # COURSES family
                elif countType == "COURSES":
                    keysToKeep += ["courses", "categories"]

                    # Subfamilies
                    if type_ == "MINIMUM":
                        prereqObj["type"] = "COURSES_MIN"
                        keysToKeep += ["count"]
                    elif type_ == "LIST":
                        prereqObj["type"] = "COURSES_LIST"
                    elif type_ == "GROUPMINIMUM":
                        prereqObj["type"] = "COURSES_GROUPMIN"
                        keysToKeep += ["count"]

                    listOfReqsStr = f" {connector} ".join(requisiteCodes)
                    prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                    prereqObj["courses"] = courses
                    prereqObj["categories"] = categories

                # FCES family
                elif countType == "FCES":
                    keysToKeep += ["courses", "categories"]
                    
                    # Subfamilies
                    if type_ == "MINIMUM":
                        prereqObj["type"] = "FCES_MIN"
                        keysToKeep += ["count"]
                    elif type_ == "LIST":
                        prereqObj["type"] = "FCES_LIST"
                    elif type_ == "MAXIMUM":
                        prereqObj["type"] = "FCES_MAX"
                        keysToKeep += ["count"]
                    elif type_ == "GROUPMINIMUM":
                        prereqObj["type"] = "FCES_GROUPMIN"
                        keysToKeep += ["count"]
                    
                    listOfReqsStr = f" {connector} ".join(requisiteCodes)
                    prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                    prereqObj["courses"] = courses
                    prereqObj["categories"] = categories

                    if prereqObj["type"] == "FCES_LIST" and categories != []:
                        print(courseFile)

                # SUBJECT_POSTS family - only one relevant here
                elif countType == "SUBJECT_POSTS" and type_ == "MINIMUM":
                    keysToKeep += ["count", "programs"]

                    prereqObj["type"] = "PROGRAM_MIN"
                    listOfReqsStr = f" {connector} ".join(requisiteCodes)
                    prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                    prereqObj["programs"] = programs

                # Whatever else
                else:
                    print(countType, type_)
                    listOfReqsStr = f" {connector} ".join(requisiteCodes)
                    prereqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()

            # Delete everything else
            for key in list(prereqObj.keys()):
                if key not in keysToKeep:
                    del prereqObj[key]

            # Collapse multiple spaces in description
            prereqObj["description"] = ' '.join(prereqObj["description"].split())

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
