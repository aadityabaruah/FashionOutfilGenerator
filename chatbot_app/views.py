from django.shortcuts import render
from django.http import JsonResponse
import os
import asyncio
from sydney import SydneyClient
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import re
import datetime
import requests
from PIL import Image
import io


def generate_unique_folder_name():
    now = datetime.datetime.now()
    return now.strftime('%Y%m%d%H%M%S')


def chat_interface(request):
    return render(request, 'chat_interface.html')


async def get_response_from_sydney(message: str) -> str:
    async with SydneyClient(style="creative") as sydney:
        response_text = ""
        async for response in sydney.ask_stream(message):
            response_text += response
    return response_text


def remove_html_tags(text):
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)


def extract_three_paragraphs(text):
    paragraphs = text.split("\n\n")
    three_paragraphs = paragraphs[:3]
    return "\n\n".join(three_paragraphs)


def extract_ideas(message: str):
    ideas = []
    lines = message.split("\n")
    for line in lines:
        if line.startswith('-'):
            idea = line.strip('- ').split('[^')[0].strip()
            ideas.append(idea)
    return ideas


API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": "Bearer hf_..."}


def query_hf_image(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.content


def send_message(request):
    os.environ['BING_U_COOKIE'] = ''
    message = request.POST.get('message')
    print(f"Received message: {message}")
    # message = "Give me ideas for a dress" + message

    response = asyncio.run(get_response_from_sydney(message))
    response = response.replace('Bing', 'Sydney')
    response = response.replace('Microsoft', 'AdiTech')

    # Check if the prefix "Hi, this is Sydney." has been shown before and remove if necessary
    if request.session.get('shown_prefix', False):
        response = response.replace("Hi, this is Sydney.", "").strip()
    else:
        request.session['shown_prefix'] = True

    # Convert Markdown bold to HTML bold
    response = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", response)
    response = re.sub(r"\[\^\d\^\]", "", response)
    response = re.sub(r'\[.*?\]', '', response)
    response = re.sub(r'\^\d\^', '', response)
    response = re.sub(r'\(.*?\)', '', response)
    response = extract_three_paragraphs(response)

    ideas = extract_ideas(response)
    return JsonResponse({"response": response, "ideas": ideas})


def generate_images_for_idea(request):
    idea = request.POST.get('idea')
    file_storage = FileSystemStorage(location=settings.OUTPUT_DIR)
    image_urls = []

    if idea:
        unique_folder = generate_unique_folder_name()
        output_directory = os.path.join(settings.MEDIA_ROOT, unique_folder)
        os.makedirs(output_directory, exist_ok=True)
        message = remove_html_tags(idea)
        message = "Face to foot image" + message

        for i in range(4):
            message = " " + message
            image_bytes = query_hf_image({"inputs": message})
            image = Image.open(io.BytesIO(image_bytes))
            image_name = f"{i}.jpeg"
            image_path = os.path.join(output_directory, image_name)
            image.save(image_path)
            rel_image_path = os.path.join("media", unique_folder, image_name)
            image_urls.append(rel_image_path)

    return JsonResponse({"image_urls": image_urls})
