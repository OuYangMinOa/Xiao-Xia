
from urllib.parse import quote      
from bs4          import BeautifulSoup

import re
import urllib



def DuckDuckSearchCommand(key):
    """Search on duckduckgo

    Args:
        key (str): keyword to search

    Returns:
        str: Search results
    """
    query = quote(key)
    site = urllib.request.urlopen("http://duckduckgo.com/html/?q="+query+'&kl=tw-tzh')
    data = site.read()
    soup = BeautifulSoup(data, "html.parser")
    my_list = soup.find("div", {"id": "links"}).find_all("div", {'class': re.compile('.*web-result*.')})[0:10]
    (result__snippet, result_url) = ([] for i in range(2))

    for i in my_list:         
        try:
            result__snippet.append(i.find("a", {"class": "result__snippet"}).get_text().strip("\n").strip())
            # print(result__snippet[-1])
        except:
            result__snippet.append(None)
        try:
            result_url.append(i.find("a", {"class": "result__url"}).get_text().strip("\n").strip())
        except:
            result_url.append(None)
    return "\n".join(result__snippet)

# print(result__snippet)


if __name__ == "__main__":
    duckduckSearch("weather")