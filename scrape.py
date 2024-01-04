from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def scrape(name, team):
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox') # required for replit
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--ignore-certificate-error")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://www.dailyfaceoff.com/teams/{team}/line-combinations")

    lines = driver.find_elements(By.XPATH, "//section[@id='line_combos']") # all the combos
    # defensemen use class="w-1/2"
    forwards = driver.find_elements(By.XPATH, "//div[contains(@class, 'w-1/3')]")[3:15]
    names = [player.get_attribute('innerText') for player in forwards]
    for i in range(0, 12, 3):
        for j in range(3):
            if name.lower() == names[i + j].lower():
                return names[i: i + 3]
    driver.quit()



if __name__ == '__main__':
    print(scrape("Ryan O'Reilly", "nashville-predators"))
