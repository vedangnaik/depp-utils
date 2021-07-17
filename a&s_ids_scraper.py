#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import re
import argparse
from pathlib import Path

# Set up argument parsing
parser = argparse.ArgumentParser(description='Scrapes course and program IDs from https://artsci.calendar.utoronto.ca/listing-program-subject-areas.')
parser.add_argument('chromedriver_path', type=Path, help="path to a valid chromedriver executable")
parser.add_argument('--c_ids_file', type=argparse.FileType('w'), help="path to ASCII file to store scraped course IDs. default: ./course-ids.txt", default="./course-ids.txt", metavar='file')
parser.add_argument('--p_ids_file', type=argparse.FileType('w'), help="path to ASCII file to store scraped program IDs. default: ./program-ids.txt", default="./program-ids.txt", metavar='file')

# Chromedriver options
options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1920x1080')

if __name__ == "__main__":
    args = parser.parse_args()

    # Set up the driver
    driver = webdriver.Chrome(executable_path=args.chromedriver_path, options=options)
    driver.get("https://artsci.calendar.utoronto.ca/listing-program-subject-areas")

    # Get the div containing all the tables.
    alphabetProgramTables = driver.find_element_by_css_selector("#block-fas-content > div > article > div > div").find_elements_by_tag_name('table')

    # Get all links in all the tables first. The <a>s themselves will expire if we go to each link and then come back, but the links will remain constant.
    subjectAreaLinks = []

    for table in alphabetProgramTables:
        # The first link in each alphabet's table is the one that scrolls the table to the top when that alphabet is clicked i.e. clicking 'B' at the top brings the #B <a> to the top.
        for a in table.find_elements_by_tag_name('a')[1:]:
            subjectAreaLinks.append(a.get_attribute('href'))

    # A few subject areas all link to the same page. Notably, these include those offered by colleges such as Trinity, University, etc. which all link to the respective college's page. Thus, we scrape some courses multiple times. This is to prevent such duplicates.
    coursesSeen = []
    cRegex = re.compile('^[A-Z]{3}[1-4][0-9]{2}[HY][01]$')
    # To weed out duplicate program IDs, just in case they come up somehow.
    programsSeen = []
    pRegex = re.compile('^AS(MAJ|SPE|MIN|FOC)[0-9]{4}.?$')

    for link in subjectAreaLinks:
        driver.get(link)

        # This xpath always leads to the elements which contain the names of the courses.
        coursesPs = driver.find_elements_by_xpath('//*[@id="block-fas-content"]/div/div/div/div[3]/div[2]/div[3]/div/p')

        # This xpath always leads to the elements which contain the names of the programs.
        programPs = driver.find_elements_by_xpath('//*[@id="block-fas-content"]/div/div/div/div[3]/div[1]/div[2]/div/p')
        
        for p in coursesPs:
            # There's a space before the actual course ID, so we extract the first to ninth letters and output to stdout.
            courseID = p.get_attribute('innerText')[1:9]
            if cRegex.match(courseID) and courseID not in coursesSeen:
                coursesSeen.append(courseID)
                args.c_ids_file.write(courseID + "\n")
            else:
                print(f"Course {courseID} is a duplicate or failed the course ID regex.", file=sys.stderr)

        for p in programPs:
            # The program ID comes at the end of the full name, after the last '-' character. Some incomplete sentences do not have any ID at all, so these are ignored. We use a regex to see whether the program IDs match.
            programID = p.get_attribute('innerText').split("-")[-1][1:]
            if pRegex.match(programID) and programID not in programsSeen:
                programsSeen.append(programID)
                args.p_ids_file.write(programID + "\n")
            else:
                print(f"Program {programID} is a duplicate or failed the program ID regex.", file=sys.stderr)

    # Print some diagnostics
    print("Finished.")
    print(f"Examined {len(subjectAreaLinks)} subject areas and scraped:")
    print(f"\t{len(coursesSeen)} course(s)")
    print(f"\t{len(programsSeen)} program(s)")

    # Close stuff
    args.c_ids_file.close()
    args.p_ids_file.close()
    driver.close()
    driver.quit()