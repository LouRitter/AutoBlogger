import openai
from dotenv import load_dotenv
import requests
import os
import random
import logging
from datetime import datetime

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set up API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Customizable settings
INCLUDE_TOPICS = ["custom homes", "design build", "home construction design", "home remodeling", "interior design"]
EXCLUDE_TOPICS = ["politics", "legal issues", "controversial subjects", "green building"]
DEFAULT_TOPIC = "Trends in Design Build Construction"
PAST_TOPICS_FILE = "past_topics.txt"
COMPANY_WEBSITE = "https://emersonbros.com"

openai.api_key = OPENAI_API_KEY

# Function to avoid duplicate topics
def get_unique_topic(include=None, exclude=None, default_topic=DEFAULT_TOPIC):
    try:
        # Load past topics
        if os.path.exists(PAST_TOPICS_FILE):
            with open(PAST_TOPICS_FILE, "r") as file:
                past_topics = file.read().splitlines()
        else:
            past_topics = []

        # Keep only the last 5 topics to avoid recent duplicates
        recent_topics = past_topics[-5:]

        # Generate new topic until it's unique
        topic = None
        attempts = 0
        while attempts < 5:  
            topic_prompt = f"Generate a unique trending blog topic about {random.choice(include)}."
            if exclude:
                topic_prompt += f" Avoid the following topics: {', '.join(exclude)}."
            if recent_topics:
                topic_prompt += f" Ensure the topic is different from the following recent topics: {', '.join(recent_topics)}."

            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a blog topic suggestion expert."},
                    {"role": "user", "content": topic_prompt}
                ],
                temperature=1.1  # Increased randomness
            )
            topic = response.choices[0].message.content.strip()

            if topic not in past_topics:
                break
            attempts += 1

        # Save the new topic
        with open(PAST_TOPICS_FILE, "a") as file:
            file.write(topic + "\n")

        logging.info(f"Selected Topic: {topic}")
        return topic
    except Exception as e:
        logging.error(f"Error generating topic: {e}")
        return default_topic

TOPIC = get_unique_topic(include=INCLUDE_TOPICS, exclude=EXCLUDE_TOPICS)

# Writing styles to add variety
styles = [
    "Write as a storytelling narrative with real-world examples.",
    "Use a research-driven approach with data and case studies.",
    "Write an engaging step-by-step tutorial on the topic.",
    "Create a listicle format with key takeaways.",
    "Provide a historical perspective on how the topic has evolved.",
    "Write a pros-and-cons analysis comparing different approaches.",
    "Offer a troubleshooting guide for common issues related to the topic.",
    "Create a future trends forecast based on industry insights.",
    "Write a 'myth vs. reality' breakdown for common misconceptions.",
    "Offer a beginner’s guide covering all the basics of the topic."
]
structure_prompt = random.choice(styles)

# Function to fetch an image from Unsplash
def fetch_image(query):
    try:
        query = query.replace(" ", "+")
        response = requests.get(
            f"https://api.unsplash.com/photos/random?query={query}&client_id={UNSPLASH_ACCESS_KEY}"
        )
        if response.status_code == 200:
            return response.json().get("urls", {}).get("regular", "")
    except Exception as e:
        logging.error(f"Error fetching image: {e}")
    return ""

image_url = fetch_image(query=TOPIC)

# Generate blog content in Markdown format
blog_prompt = f"""
Write a 1000-word blog post in Markdown format about {TOPIC}. 
Ensure the information is up-to-date for {datetime.now().year} and avoid outdated references from past years.
Make sure each response is unique and follows this writing style: {structure_prompt}.

Include a section at the end with contact information for Emerson Brothers Construction, found at {COMPANY_WEBSITE}, along with a description of their services.
"""

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a professional blog writer for Emerson Brothers Construction who writes in Markdown format."},
        {"role": "user", "content": blog_prompt}
    ],
    temperature=0.9,  
    frequency_penalty=0.4,  
    presence_penalty=0.3
)

blog_content = response.choices[0].message.content.strip()

# Save blog post as an HTML file with Markdown formatting
def save_blog(content, filename_prefix="blog"):
    file_name = f"{filename_prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
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
        blockquote {{ font-style: italic; margin-top: 20px; }}
        pre, code {{ background: #f4f4f4; padding: 10px; border-radius: 5px; display: block; }}
    </style>
</head>
<body>
    <article>
        <h1>{TOPIC}</h1>
        {f'<img src="{image_url}" alt="{TOPIC}">' if image_url else ''}
        {content.replace('\n', '<br>')}
    </article>
</body>
</html>
"""
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(html_content)
    logging.info(f"Blog post saved as {file_name}")

save_blog(blog_content)
