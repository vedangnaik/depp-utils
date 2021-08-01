import re

# For every A&S course across all campuses
allCoursesRe = re.compile('[A-Z]{3}[A-Z0-9][0-9]{2,3}[HY][0-9]?')

# For all specific programs like major, minor, specialist, etc.
allProgramsRe = re.compile('AS(MAJ|SPE|MIN|FOC|CER)([0-9]{4}).?')

# For identifying program requirements
requirementRe = re.compile('Req[0-9]{1,3}')

# For identifying course prerequisite IDs
prerequisiteRe = re.compile('P[0-9]{1,3}')

# For all St. George courses only
stGeorgeCoursesRe = re.compile('[A-Z]{3}[0-9]{3}[HY][01]')