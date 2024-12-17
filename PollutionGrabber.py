import time
import traceback
from time import sleep

import selenium
import selenium.webdriver
import shutil
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def wait_for_vis(driver, target_id, timeout=30, by_val=By.CSS_SELECTOR):
    wait = WebDriverWait(driver, timeout)
    ret = wait.until(EC.visibility_of_element_located((by_val, target_id)))
    return ret

def wait_and_get(driver, target_id, timeout=30, by_val=By.ID):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.presence_of_element_located( (by_val, target_id) ))

def wait_and_get_vis_vals(driver, target_id, timeout=30, by_val=By.ID):
    wait = WebDriverWait(driver, timeout)
    return wait.until(EC.visibility_of_all_elements_located( (by_val, target_id) ))

def make_selection(driver, list_name, visible_choice):
    select = Select(wait_and_get(driver, list_name))

    # wait for option to be present or timeout
    wait = WebDriverWait(driver, 30)
    is_choice_present = lambda d : is_option_present(select, visible_choice)
    wait.until(is_choice_present)

    select.select_by_visible_text(visible_choice)

def is_option_present(select : Select, visible_choice):
    for element in select.options:
        if element.text == visible_choice:
            return True

def is_downloading(driver):
    top_download : WebElement = get_top_download(driver)
    curr_down_desc : list[WebElement] = top_download.shadow_root.find_elements(By.CSS_SELECTOR, "div[class='description']")
    for element in curr_down_desc:
        if element.is_displayed():
            return True

    return False

# spread out for debugging purposes; assumes driver is on chrome downloads url already
def get_top_download(driver):
    curr_down : WebElement = wait_and_get(driver, "//downloads-manager", by_val=By.XPATH)
    curr_down = curr_down.shadow_root.find_element(value="downloadsList") # does find shadow root
    curr_down = curr_down.find_element(value="list")
    curr_down = curr_down.find_element(value="frb0")
    return curr_down


def pollution_grabber():
    # inclusive start and end dates
    pollutants = ["Ozone"]
    year_start = 1983
    year_end = 2024
    city_list = ["San Francisco-Oakland-Hayward, CA", "Los Angeles-Long Beach-Anaheim, CA", "San Diego-Carlsbad, CA", "Fresno, CA"]
    city_list.sort()

    year_range = range(max(1980, year_start), year_end + 1)
    for pollutant in pollutants:
        for city in city_list:
            # ensure files downloaded to correct location
            out_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", pollutant, city)
            options = selenium.webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-setuid-sandbox")

            options.add_argument("--remote-debugging-port=9222")  # this

            options.add_argument("--disable-dev-shm-using")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")
            options.add_argument("start-maximized")
            options.add_argument("disable-infobars")
            options.add_argument(r"user-data-dir=.\cookies\\test")
            prefs = {"download.default_directory" : out_dir, "profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)

            # start driver
            driver = selenium.webdriver.Chrome(options=options)
            for year in year_range:
                driver.get("https://www.epa.gov/outdoor-air-quality-data/download-daily-data")
                try:
                    # select each category and the desired option
                    make_selection(driver, 'poll', pollutant)
                    make_selection(driver, 'year', str(year))
                    make_selection(driver, 'cbsa', city)

                    # have website create link
                    button = wait_for_vis(driver, "input[value=\'Get Data\']", by_val=By.CSS_SELECTOR)
                    time.sleep(2) # if you don't wait on the button it errors out
                    button.click() # Create data link

                    # get link
                    link = wait_for_vis(driver, "//div[@id=\'results\']/p/a", by_val=By.XPATH)
                    link.click() # download the csv file

                    # use link to get filename
                    link = link.get_property("href")
                    filename = link[link.find("ad_viz") : link.find(".sas", 0, len(link))]
                    filepath = os.path.join(out_dir, filename + ".csv")

                    # wait for download before closing
                    driver.get("chrome://downloads") #
                    try:
                        while is_downloading(driver):
                            sleep(2) # wait for download to finish
                    except Exception as e:
                        print("Got Exception checking downloads of: \n")
                        e.with_traceback()


                except Exception as e:
                    print("Got Exception: \n")
                    e.with_traceback()
                    print(" -for {" + pollutant + ", " + city + ", " + year + "}.")

                # end year loop

            driver.close()
            # end city loop

        # end pollution loop

    # end def


if __name__ == '__main__':
    try:
        pollution_grabber()
    except Exception as e:
        # printl("EPAPollutionGrabber execution failed; printing exception: \n" + str(e))
        # printl("Full stack trace \n")
        traceback.print_exc()
