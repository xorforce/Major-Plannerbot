from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
opts = Options()
opts.set_headless()
assert opts.headless
browser = Firefox(options=opts)

activity = "parasailing"
place = "bangalore"

url = "https://lbb.in/" + place + "/search/?s=" + activity
print(url)


browser.get(url)

for _ in range(100):
    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# print all of the page source that was loaded
soup = BeautifulSoup((browser.page_source.encode("utf-8")))

items = soup.findAll("div", {"class": "cardAlgolia"})

for item in items:
    card = item.find("div", {"class": "cardAlgolia__locality ng-scope"})
    try:
        location = str(card.find("span", {"class": "first ng-binding"}))
        actual_name = str(item.find("span", {"class": "trackTitle ng-binding"}))
        
        location = (location.split("</")[0]).split("binding\">")[1]
        actual_name = (actual_name.split("</")[0]).split("binding\">")[1]
        print(location.strip())
        print(actual_name.strip())
        print("\n")
    except:
        pass