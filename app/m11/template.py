from app.utility.soup import get_soup, BeautifulSoup

def parse_elements(template: str, url: str) -> str:
    soup = get_soup(template)
    ref: BeautifulSoup
    for ref in soup(["m11:element"]):
        attributes = ref.attrs
        print(f"ELEMENT NAME: {attributes["name"]}")
        attrs = {
            "href": "#", 
            "hx-get": f"{url}/{attributes["name"]}",
            "hx-target": "#specificationSection", 
            "hx-swap": "outerHTML"
        }
        link = soup.new_tag("a", attrs=attrs)
        ref.replace_with(link)
        link.append(attributes["name"])
    return str(soup)


