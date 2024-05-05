import http.client
import json
import ssl
import time


# Create a new SSL context with certificate verification disabled
def query_signal(cursor: str):
    ssl_context = ssl._create_unverified_context()

    conn = http.client.HTTPSConnection("signal-api.nfx.com", context=ssl_context)

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
        "Content-Type": "application/json",
    }

    payload = '{"query":"query vclInvestors($slug: String!, $after: String) {\\n  list(slug: $slug) {\\n    scored_investors(first: 8, after: $after) {\\n      pageInfo {\\n        hasNextPage\\n        hasPreviousPage\\n        endCursor\\n      }\\n      record_count\\n      edges {\\n        node {\\n          ...investorListInvestorProfileFields\\n        }\\n      }\\n    }\\n  }\\n}\\n\\nfragment investorListInvestorProfileFields on InvestorProfile {\\n  id\\n  person {\\n    first_name\\n    last_name\\n    slug\\n    linkedin_url\\n    facebook_url\\n    twitter_url\\n    crunchbase_url\\n    angellist_url\\n    url\\n  }\\n  investor_profile_funding_rounds {\\n    record_count\\n  }\\n  position\\n  min_investment\\n  max_investment\\n  target_investment\\n  location {\\n    display_name\\n  }\\n  firm {\\n    name\\n  }\\n  investment_locations {\\n    display_name\\n  }\\n  investor_lists {\\n    stage_name\\n    vertical {\\n      display_name\\n    }\\n  }\\n  investments_on_record(first: 20) {\\n    pageInfo {\\n      hasNextPage\\n    }\\n    record_count\\n    edges {\\n      node {\\n        company_display_name\\n      }\\n    }\\n  }\\n}\\n","variables":{"slug":"marketplaces-seed","after":"MTY"}}'.replace(
        "MTY", cursor
    )

    conn.request("POST", "/graphql", payload, headers)

    res = conn.getresponse()
    data = res.read()

    json_response = (
        json.loads(data.decode("utf-8"))
        .get("data")
        .get("list")
        .get("scored_investors")
        .get("edges")
    )

    next_cursor = (
        json.loads(data.decode("utf-8"))
        .get("data")
        .get("list")
        .get("scored_investors")
        .get("pageInfo")
        .get("endCursor")
    )
    has_next = (
        json.loads(data.decode("utf-8"))
        .get("data")
        .get("list")
        .get("scored_investors")
        .get("pageInfo")
        .get("hasNextPage")
    )

    with open("signal_investor_urls.jsonl", "a") as file:
        for item in json_response:
            # with open("signal_investor_test.jsonl", "a") as file:
            #     file.write(json.dumps(item.get("node")) + ",\n")
            # investor_url = "https://signal.nfx.com/investors/" + item.get("node").get(
            #     "person"
            # ).get("slug")

            first_name = (
                item.get("node").get("person").get("first_name")
                if item.get("node").get("person").get("first_name")
                else ""
            )

            last_name = (
                item.get("node").get("person").get("last_name")
                if item.get("node").get("person").get("last_name")
                else ""
            )

            min_investment = item.get("node").get("min_investment")
            max_investment = item.get("node").get("max_investment")

            firm_name = item.get("node").get("firm")
            if firm_name:
                firm_name = firm_name.get("name")

            location = item.get("node").get("location")
            if location:
                location = location.get("display_name")

            investor_list = item.get("node").get("investor_lists")

            industry_list = set(
                item.get("vertical").get("display_name")
                for item in investor_list
                if item.get("stage_name") != "Other Lists"
            )
            industries = ", ".join(industry_list)

            investment_on_record_list = (
                item.get("node").get("investments_on_record").get("edges")
            )

            if investment_on_record_list:
                for item in investment_on_record_list:
                    round_on_investment_record = item.get("node").get(
                        "investor_profile_funding_rounds"
                    )
                    if round_on_investment_record:
                        round_list = set(
                            value.get("funding_round").get("stage")
                            for value in round_on_investment_record
                        )

                        rounds = ", ".join(round_list)
                    else:
                        round_list = set(
                            item.get("stage_name")
                            for item in investor_list
                            if item.get("stage_name") != "Other Lists"
                        )
                        rounds = ",".join(round_list)
            else:
                round_list = set(
                    item.get("stage_name")
                    for item in investor_list
                    if item.get("stage_name") != "Other Lists"
                )
                rounds = ", ".join(round_list)

            if investment_on_record_list:
                investment_on_record = [
                    item.get("node").get("company_display_name")
                    for item in investment_on_record_list
                ]
            else:
                investment_on_record = []

            notable_investments = ", ".join(investment_on_record)

            linkedin_url = (
                item.get("node").get("person").get("linkedin_url")
                if item.get("node").get("person")
                else ""
            )

            twitter_url = (
                item.get("node").get("person").get("twitter_url")
                if item.get("node").get("person")
                else ""
            )

            website_url = (
                item.get("node").get("person").get("url")
                if item.get("node").get("person")
                else ""
            )

            obj = {
                "first_name": first_name,
                "last_name": last_name,
                "firm_name": firm_name,
                "position": item.get("node").get("position"),
                "min_investment": min_investment,
                "max_investment": max_investment,
                "location": location,
                "twitter": twitter_url,
                "linkedin": linkedin_url,
                "website": website_url,
                "notable_investments": notable_investments,
                "rounds": rounds,
                "industries": industries,
            }
            file.write(json.dumps(obj) + ",\n")

    if has_next:
        time.sleep(3)
        query_signal(next_cursor)


if __name__ == "__main__":
    query_signal("OA")
