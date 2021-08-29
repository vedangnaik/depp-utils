#!/usr/bin/env python3

import json
import glob
import argparse
from pathlib import Path
import re

from constants import allCoursesRe, allProgramsRe, requirementRe

# Set up argument parsing
parser = argparse.ArgumentParser(description="Aggregates and cleans program JSON objects downloaded from https://degreeexplorer.utoronto.ca/.")
parser.add_argument("--p_jsons_dir", type=str, help="path to directory to read downloaded program JSONs from. default: ./program_data", default="./program_data", metavar="dir")
parser.add_argument("--p_aggr_file", type=argparse.FileType("w"), help="path to file to write aggregated programs into. default: ./aggregated_programs.json", default="./aggregated_programs.json", metavar="file")
parser.add_argument("--debug", help="include to pretty-print JSON. Useful for debugging.", action="store_true")

# Dict to hold final aggregated JSON obj
aggregated_programs = {}
a = []

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

        # # For each requirement, first bring the embedded requirement object a level higher and make it a dict instead of a list
        newReqs = {}
        for reqObj in programObj["detailAssessments"]:
            # Bring the main requirement object one level higher
            reqObj['requirement']['count'] = reqObj['credits']['requiredCredits']
            reqObj = reqObj["requirement"]
            # Extract some useful info
            reqID = reqObj["shortIdentifier"][1:-1]
            displayPrefix = reqObj["displayPrefix"]
            connector = reqObj["subItemConnectorString"]
            displaySuffix = reqObj["displaySuffix"]
            type_ = reqObj["type"]
            # We need the actual codes of each requisiteItem to make the display string
            requisiteCodes = []

            # For each requisite item, we only need the code and the type of the code i.e. course, program, or category, or another prereq. We will group them via these labels.
            courses = []
            programs = [] # There are actually no programs in any of the requirements, but this is just left in for completion's sake.
            categories = []
            dependentReqs = []
            for i in range(len(reqObj["requisiteItems"])):
                code = reqObj["requisiteItems"][i]["code"]
                requisiteCodes.append(code)
                if allCoursesRe.match(code):
                    courses.append(code)
                elif allProgramsRe.match(code):
                    programs.append(code)
                elif requirementRe.match(code):
                    dependentReqs.append(code)
                else:
                    categories.append(code)

            # Now, we proceed differently depending on what types and other factors this requirement has.
            # Array of reqObj keys to keep.
            keysToKeep = ["description", "type"]
            # REUSE doesn't really affect anything, since even if courses are not reused, it doesn't matter. Hence, we simply return COMPLETE for this.
            if type_ == "REUSE":
                reqObj["type"] = "NOTE"
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                reqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()

            # COMPLEX types are usually not verifiable.
            elif type_ == "COMPLEX":
                reqObj["type"] = "UNVERIFIABLE"
                reqObj["description"] = displayPrefix.strip()

            # NOTE objects need nothing more than the description
            elif type_ == "NOTE":
                reqObj["type"] = "NOTE"
                reqObj["description"] = displayPrefix.strip()

            # MINIMUM requirements are split between recursive requirement ones and non-recursive courses/categories ones, even though this isn't specifically mentioned anywhere in the object.
            elif type_ == "MINIMUM":
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                reqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()

                # Remove minimum grade ones, don't ask why the hell they're in here.
                if "Grade" in displayPrefix:
                    reqObj["type"] = "UNVERIFIABLE"
                else:
                    match = re.compile("At least ([0-9]*.*[0-9]*) (Course|Credit|Requirement)").search(displayPrefix)
                    if match:
                        # Used to easily select the right type (vs. if-else).
                        constraintTypes = {
                            "Course": "NUM",
                            "Credit": "FCES",
                            "Requirement": "REQS"
                        }
                        # Used to assemble the final new type more easily.
                        requisiteTypes = ""
                        # Recreate the count from the prefix; it is missing for both requirements and courses. Yeah, don't ask why.
                        reqObj["count"] = match.group(1)
                        keysToKeep += ["count"]
                        # FYI: Requirements and courses/categories are exclusive.
                        if len(dependentReqs) != 0 and match.group(2) == "Requirement":
                            requisiteTypes += "REQUIREMENTS_"
                            reqObj["dependentReqs"] = dependentReqs
                            keysToKeep += ["dependentReqs"]
                        if len(courses) != 0:
                            requisiteTypes += "COURSES_"
                            reqObj["courses"] = courses
                            keysToKeep += ["courses"]
                        if len(categories) != 0:
                            requisiteTypes += "CATEGORIES_"
                            reqObj["categories"] = categories
                            keysToKeep += ["categories"]
                        reqObj["type"] = f"{requisiteTypes[:-1]}/{constraintTypes[match.group(2)]}/MIN"
                    
                    # Shouldn't happen, just in case.
                    else:
                        print(f"{type_}: Unknown prefix '{displayPrefix}' in {programFile}, {reqID}")
                        reqObj["type"] = "UNVERIFIABLE"

            # LIST means every single item mentioned must be present. Only courses are present in list requirements. Verified via explicit checking of all programs. 
            elif type_ == "LIST":
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                reqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                # Straight away hardcode to the new type.
                reqObj["type"] = "COURSES/NUM/LIST"
                reqObj["courses"] = courses
                keysToKeep += ["courses"]

            # NO_REUSE prohibits the sharing of courses across the listed requirements. Only other requirements are present. Verified via explicit checking of all programs.
            elif type_ == "NO_REUSE":
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                reqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                # Hardcode the new type.
                reqObj["type"] = "REQUIREMENTS/NUM/NO_REUSE"
                reqObj["dependentReqs"] = dependentReqs
                keysToKeep += ["dependentReqs"]

            # GROUPMINIMUMs are like MINIMUMS but place restrictions upon the used courses of other requirements. Unfortunately, some of these refer to requirements that are ahead of this one. Thus, these are handled in a second loop.
            elif type_ == "GROUPMINIMUM" or type_ == "GROUPMAXIMUM":
                listOfReqsStr = f" {connector} ".join(requisiteCodes)
                reqObj["description"] = f"{displayPrefix} {listOfReqsStr} {displaySuffix}".strip()
                # There are no such requirements which recursively combine requirements with others. Only courses/categories have been seen so far. Verified via explicit checking of all programs.
                match = re.compile("(At least|No more than) ([0-9]*.*[0-9]*) (Course|Credit)").search(displayPrefix)
                if match:
                    # Recreate the count. Some of them have it correctly, but eh.
                    reqObj["count"] = float(match.group(2))
                    keysToKeep += ["count"]
                    # string for new type
                    requisiteTypes = ""

                    if len(courses) != 0: 
                        requisiteTypes += "COURSES_"
                        reqObj["courses"] = courses
                        keysToKeep += ["courses"]
                    if len(categories) != 0:
                        requisiteTypes += "CATEGORIES_"
                        reqObj["categories"] = categories
                        keysToKeep += ["categories"]
                    # Depending on whether it's credits or courses, fix the type. For courses, the 'count' key does not report accurate information (as usual), so recreate that too (although here we're just doing it for all *shrug*).
                    reqObj["type"] = f"{requisiteTypes[:-1]}/{'NUM' if match.group(3) == 'Course' else 'FCES'}/{type_[:8]}"

                    # Add recurs requirements by parsing suffix.
                    reqObj["recursReqs"] = requirementRe.findall(displaySuffix)
                    keysToKeep += ["recursReqs"]


                # ATM, these don't exist. Just in case.
                else:
                    print(f"{type_}: Unknown prefix '{displayPrefix}' in {programFile}, {reqID}")
                    reqObj["type"] = "UNVERIFIABLE"

            # There shouldn't be any others. This is just in case.
            else:
                print(type_)

            # Remove unwanted keys
            for key in list(reqObj.keys()):
                if key not in keysToKeep:
                    del reqObj[key]

            # Collapse multiple spaces in description
            reqObj["description"] = " ".join(reqObj["description"].split())
            # Done, add it to the new dict
            newReqs[reqID] = reqObj

        # Now that we have finished modifying everything, we add the new prereqs to the courseObj and append this to the final file
        programObj["detailAssessments"] = newReqs
        aggregated_programs[Path(programFile).stem] = programObj


    # We have finished modifying all the courses. Write aggregated_courses to file
    if (args.debug):
        json.dump(aggregated_programs, args.p_aggr_file, ensure_ascii=False, indent=2)
    else:
        json.dump(aggregated_programs, args.p_aggr_file, ensure_ascii=False, separators=(",", ":"))

    # Print diagnostics
    print("Finished.")
    print(f"Cleaned and aggregate {attempted} course(s) from {args.p_jsons_dir}")

    args.p_aggr_file.close()