# depp-utils
A collection of utility scripts to scrape course and program data from University of Toronto websites for Degree Explorer++.

## Usage

To begin, install the requirements with `pip install -r requirements.txt`.

The flowchart below succinctly explains how the 7 main Python scripts in this repository interact. The goal of the scraping process is to produce `aggregated_courses.json`, `aggregated_programs.json`, and `aggregated_course_categories.json`, marked in green. These JSON files are then loaded into the `resources` folder in Degree Explorer++ for use by the site. Currently, these JSONs are converted into plain JS files for easy loading via the JS static import system. This is as simple as changing the file extension from `.json` to `.js` and adding `export default` to the front of the object. These may be migrated to asynchronous fetches in the future, in which case this extra manual transformation will not be necessary.

![Untitled-2021-08-31-2104](https://user-images.githubusercontent.com/25436568/131538195-8b508b55-2f4d-445c-bbfd-080bf9d2f8ab.png)

Please type `python <script name> --help` to see some command-line options that control the file and folder names. Notably, `a&s_ids_scraper.py` requires a Selenium Webdriver to do the scraping. Only *chromedriver* has been tested for now, but any modern browser should work fine.
