from openai import OpenAI
from scraper import fetch_website_links, fetch_website_contents
import json

# Rich Markdown rendering
from rich.console import Console
from rich.markdown import Markdown

console = Console()


# MODEL CONFIG


MODEL = "llama3.1:8b"

client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)





link_system_prompt = """ 
You are provided with a list of links found on a webpage.

You decide which links are most relevant to include in the brochure about the company,
such as About pages, Company pages, or Careers pages.

Respond ONLY in JSON format like:

{
    "Links": [
        {"type": "about page", "url": "https://example.com/about"},
        {"type": "careers page", "url": "https://example.com/careers"}
    ]
}
"""

def get_links_user_prompt(url):

    user_prompt = f"""
Here is the list of links on the website {url}

Please decide which links are relevant for a brochure.

Do NOT include:
- Privacy Policy
- Terms of Service
- Email links

Links:
"""

    links = fetch_website_links(url)

    user_prompt += "\n".join(links)

    return user_prompt



# SELECT RELEVANT LINKS


def select_relevant_links(url):

    print(f"Selecting relevant links for {url} using {MODEL}")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": link_system_prompt},
            {"role": "user", "content": get_links_user_prompt(url)}
        ],
        response_format={"type": "json_object"}
    )

    result = response.choices[0].message.content

    

    try:
        links = json.loads(result)
    except json.JSONDecodeError:
        print("⚠️ JSON decode failed — returning empty links")
        links = {"Links": []}

    return links



# FETCH PAGE CONTENTS


def fetch_page_and_all_relevant_links(url):

    contents = fetch_website_contents(url)

    relevant_links = select_relevant_links(url)

    result = f"## Landing page:\n\n{contents}\n\n## Relevant links:\n"

    for link in relevant_links.get("Links", []):

       
        result += f"\n\n### Link: {link['type']}\n"

        try:
            page_content = fetch_website_contents(link["url"])
            result += page_content

        except Exception as e:
            print("Error fetching:", link["url"])
            print(e)

    return result



# BROCHURE PROMPT


brochure_system_prompt = """
You are an assistant that analyzes company webpages
and creates a short, humorous, entertaining, witty brochure.

Respond in MARKDOWN.
Do NOT use code blocks.

Include:
- Company culture
- Customers
- Careers/jobs (if available)
"""


def get_brochure_user_prompt(company_name, url):

    user_prompt = f"""
You are analyzing a company called:

{company_name}

Here are the contents of its landing page
and relevant pages:

"""

    user_prompt += fetch_page_and_all_relevant_links(url)

    # Limit size
    user_prompt = user_prompt[:5000]

    return user_prompt



# GENERATE BROCHURE


def get_brochure(company_name, url):

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": brochure_system_prompt},
            {
                "role": "user",
                "content": get_brochure_user_prompt(company_name, url)
            }
        ]
    )

    result = response.choices[0].message.content

    # Render nicely in terminal
    console.print(Markdown(result))

    # Save to file
    with open("brochure.md", "w", encoding="utf-8") as f:
        f.write(result)

    print("\n✅ Brochure saved to brochure.md")



# RUN

get_brochure(
    "Edward Donner",
    "https://edwarddonner.com/"
)