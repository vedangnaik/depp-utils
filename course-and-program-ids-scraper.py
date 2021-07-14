from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys
import re

# Set up the driver - driver path is passed in via sys.argv[1]
options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1920x1080')
driver = webdriver.Chrome(executable_path=sys.argv[1], chrome_options=options)
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
coursesSeen = {}
cRegex = re.compile('^[A-Z]{3}[1-4][0-9]{2}[HY][01]$')
# To weed out duplicate program IDs, just in case they come up somehow.
programsSeen = {}
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
            coursesSeen[courseID] = True

    for p in programPs:
        # The program ID comes at the end of the full name, after the last '-' character. Some incomplete sentences do not have any ID at all, so these are ignored. We use a regex to see whether the program IDs match.
        programID = p.get_attribute('innerText').split("-")[-1][1:]
        if pRegex.match(programID) and programID not in programsSeen:
            programsSeen[programID] = True

# Write the ids to a txt file
with open("course-ids.txt", "w") as f:
    f.writelines('\n'.join(coursesSeen.keys()))
with open("program-ids.txt", "w") as f:
    f.writelines('\n'.join(programsSeen.keys()))

driver.close()
driver.quit()