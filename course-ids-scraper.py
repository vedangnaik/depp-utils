from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import sys

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
coursesAlreadySeen = {}

for link in subjectAreaLinks[:5]:
    driver.get(link)

    # This xpath always leads to the elements which contain the names of the courses.
    coursesPs = driver.find_elements_by_xpath('//*[@id="block-fas-content"]/div/div/div/div[3]/div[2]/div[3]/div/p')
    
    for p in coursesPs:
        # There's a space before the actual course ID, so we extract the first to ninth letters and output to stdout.
        courseID = p.get_attribute('innerText')[1:9]
        if courseID not in coursesAlreadySeen:
            coursesAlreadySeen[courseID] = True
            print(courseID)