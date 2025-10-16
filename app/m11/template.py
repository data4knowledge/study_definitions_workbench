from app.utility.soup import get_soup, BeautifulSoup


def parse_elements(template: str, url: str) -> str:
    soup = get_soup(template)
    ref: BeautifulSoup
    for ref in soup(["m11:element"]):
        attributes = ref.attrs
        id = ref.parent["id"]
        attrs = {
            "hx-get": f"{url}/{attributes['name']}/link",
            "hx-trigger": "load",
            "hx-target": f"#{id}",
            "hx-swap": "outerHTML",
        }
        link = soup.new_tag("div", attrs=attrs)
        ref.replace_with(link)
        link.append(attributes["name"])
    return str(soup)
