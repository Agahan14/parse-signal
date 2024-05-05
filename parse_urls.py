import json
import re
from dataclasses import dataclass
from time import sleep

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument(
    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
)

driver = webdriver.Chrome(options=options)


def parse_investor_urls(file):
    count = 0
    with open(file) as file:
        investor_urls = file.read()
        investor_urls = json.loads(investor_urls)

    for url in investor_urls:
        count += 1

        driver.get(url)
        sleep(5)

        soup = BeautifulSoup(driver.page_source, "lxml")

        # project_name = url.split("/")[-1]

        # print(url)

        # with open(f"data/{project_name}.html", "w") as file:
        #     file.write(driver.page_source)

        # with open(f"data/{project_name}.html") as file:
        #     src = file.read()

        # soup = BeautifulSoup(src, "lxml")

        investor_full_name = soup.find("h1", class_="f3 f1-ns mv1")

        if investor_full_name:
            investor_full_name = investor_full_name.text.split("(")[0].strip()

            investor_first_name = investor_full_name.split(" ")[0]
        else:
            investor_last_name = ""
            investor_first_name = ""

        if investor_full_name:
            if len(investor_full_name.split(" ")) > 1:
                investor_last_name = investor_full_name.split(" ")[1]
            else:
                investor_last_name = ""
        else:
            investor_last_name = ""
            investor_first_name = ""

        investor_firm_name = soup.select_one(".col-xs-7 > span.lh-solid > a")

        if investor_firm_name:
            investor_firm_name = investor_firm_name.text
        else:
            investor_firm_name = ""

        investor_location = soup.find("span", class_="ml1")

        if investor_location:
            investor_location = investor_location.text
        else:
            investor_location = ""

        element = soup.select_one(".col-xs-7 > span.lh-solid")

        if element:
            for child in element.find_all():
                child.extract()
            investor_position = " ".join(element.get_text(strip=True).split())

        label_element = soup.find(
            "span", class_="section-label", string="Investments On Record"
        )

        if label_element:
            parent_element = label_element.find_parent(class_="line-separated-row")

            if parent_element:
                value_element = parent_element.find("div", class_="col-xs-7")

                if value_element:
                    investor_n_investments = value_element.text.strip()

        investment_range_element = soup.find(
            "span", class_="section-label", string="Investment Range"
        )

        if investment_range_element:
            parent_element = investment_range_element.find_parent(
                class_="line-separated-row"
            )

            if parent_element:
                value_element = parent_element.find("div", class_="col-xs-7")

                if value_element:
                    investment_range = value_element.text.strip()

        website_link = soup.select_one(".sn-linkset a[href]")

        if website_link:
            website_url = website_link["href"]
        else:
            website_url = ""

        linkedin_link = soup.select_one('.sn-linkset > a[href*="linkedin.com"]')

        if linkedin_link:
            linkedin_url = linkedin_link["href"]
        else:
            linkedin_url = ""

        twitter_link = soup.select_one('.sn-linkset > a[href*="twitter.com"]')
        if twitter_link:
            twitter_url = twitter_link["href"]
        else:
            twitter_url = ""

        round_and_industries = soup.find_all("a", class_="vc-list-chip")

        industry_list = []
        round_list = []

        round_elements = soup.find_all(class_="round-padding")

        seed_pre_seed_records = []

        for element in round_elements:
            text = element.get_text()
            if "Seed" in text or "Pre Seed" in text or "Series" in text:
                seed_pre_seed_records.append(text.strip())

        for item in seed_pre_seed_records:
            seed_match = re.search(r"(Seed|Pre\sSeed|Series\s[ABC])", item)
            if seed_match:
                seed_type = seed_match.group()
                round_list.append(seed_type)

        if round_and_industries:
            for word in round_and_industries:
                split_word = word.text.split()

                if len(split_word) > 1 and split_word[1] in [
                    "(Seed)",
                    "(Pre-seed)",
                    "(Series B)",
                    "(Series A)",
                    "(Series C)",
                ]:
                    industry_list.append(split_word[0])
                    if not round_list:
                        round_list.append(
                            split_word[1].replace("(", "").replace(")", "")
                        )

        industry_string = ", ".join(list(set(industry_list)))

        sanitized_round_list = list(set(round_list))

        if "Pre Seed" in sanitized_round_list:
            index_of_pre_seed = sanitized_round_list.index("Pre Seed")
            sanitized_round_list[index_of_pre_seed] = "Pre-seed"

        round_string = ", ".join(list(set(sanitized_round_list)))

        notable_investment_list = []
        for tr in soup.find_all("tr"):
            td = tr.find("td")
            if td:
                div = td.find("div", class_="round-padding")
                if div:
                    notable_investment_list.append(div.text)

        notable_investments = ", ".join(notable_investment_list)

        investor_data = {
            "first_name": investor_first_name,
            "last_name": investor_last_name,
            "firm_name": investor_firm_name,
            "position": investor_position,
            "n_investments": investor_n_investments,
            "website": website_url,
            "linkedin": linkedin_url,
            "twitter": twitter_url,
            "industry": industry_string,
            "rounds": round_string,
            "investment_range": investment_range,
            "location": investor_location,
            "notable_investments": notable_investments,
        }

        with open("data/investor_test.jsonl", "a", encoding="utf-8") as file:
            json.dump(investor_data, file, indent=4, ensure_ascii=False)
            file.write(",\n")

        print(count)


parse_investor_urls("signal_investor_urls.jsonl")
