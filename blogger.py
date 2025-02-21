from dotenv import load_dotenv

import openai
import requests
import os
from datetime import datetime
from bs4 import BeautifulSoup

load_dotenv()
OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY=os.environ.get("UNSPLASH_ACCESS_KEY")
INSTAGRAM_USERNAME=os.environ.get("INSTAGRAM_USERNAME")

# fetch latest Instagram posts

def get_instagram_posts(username):
    url = f"https://www.instagram.com/{username}/"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        captions = []
        for script in soup.find_all('script'):
            if 'window._sharedData' in script.text:
                json_text = script.text.split(' = ', 1)[1].rstrip(';')
                json_data = eval(json_text)
                posts = json_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
                for post in posts[:5]:  # Get latest 5 posts
                    captions.append(post['node']['edge_media_to_caption']['edges'][0]['node']['text'])
        return captions
    return []

# Get recent Instagram captions
recent_captions = get_instagram_posts(INSTAGRAM_USERNAME)
print ("Recent captions:", recent_captions)
if recent_captions:
    TOPIC = f"Trending blog topic based on Instagram posts: {recent_captions[0]}"
else:
    TOPIC = "Design, Build, and Construction: Best Practices and Trends"

# Generate blog content
openai.api_key = OPENAI_API_KEY
response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a professional blog writer."},
        {"role": "user", "content": f"Write a 1000-word blog post about {TOPIC} with SEO optimization."}
    ]
)

blog_content = response.choices[0].message.content

# Get an image from Unsplash
image_url = ""
try:
    unsplash_response = requests.get(
        f"https://api.unsplash.com/photos/random?query=construction&client_id={UNSPLASH_ACCESS_KEY}"
    )
    if unsplash_response.status_code == 200:
        image_url = unsplash_response.json().get("urls", {}).get("regular", "")
except Exception as e:
    print("Error fetching Unsplash image:", e)

# Format content into an HTML file
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{TOPIC}</title>
    <meta name="description" content="A detailed blog post about {TOPIC}">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>{TOPIC}</h1>
    {f'<img src="{image_url}" alt="{TOPIC}">' if image_url else ''}
    <article>
        {blog_content.replace('\n', '<br><br>')}
    </article>
</body>
</html>
"""

# Save as an HTML file
file_name = f"blog_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
with open(file_name, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Blog post generated and saved as {file_name}")