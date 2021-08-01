#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import re
import argparse
from pathlib import Path

from constants import stGeorgeCoursesRe, allProgramsRe

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
    numCourses = 0
    # To weed out duplicate program IDs, just in case they come up somehow.
    numPrograms = 0


    for link in subjectAreaLinks:
        driver.get(link)
        # elems = driver.find_elements_by_css_selector(".view-display-id-block_1")
        collapsiblePs = driver.find_elements_by_css_selector('.js-views-accordion-group-header')
        for p in collapsiblePs:
            text = p.get_attribute('innerText')
            c = stGeorgeCoursesRe.search(text)
            p = allProgramsRe.search(text)
            if c:
                numCourses += 1
                args.c_ids_file.write(c.group(0) + "\n")
            if p:
                numPrograms += 1
                args.p_ids_file.write(p.group(0) + "\n")

        print(f"{link}: {len(collapsiblePs)}")

    # Print some diagnostics
    print("Finished.")
    print(f"Examined {len(subjectAreaLinks)} subject areas and scraped:")
    print(f"\t{numCourses} course(s)")
    print(f"\t{numPrograms} program(s)")

    # Close stuff
    args.c_ids_file.close()
    args.p_ids_file.close()
    driver.close()
    driver.quit()