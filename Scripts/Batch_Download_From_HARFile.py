import json
import os
import requests

# HAR 文件路径
har_file_path = '123.har'

# 创建保存图片的文件夹
download_folder = 'downloaded_images'
os.makedirs(download_folder, exist_ok=True)

# 解析 HAR 文件
with open(har_file_path, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# 遍历所有请求，筛选图片
image_urls = []
for entry in har_data['log']['entries']:
    response = entry['response']
    if 'content' in response and 'mimeType' in response['content']:
        mime_type = response['content']['mimeType']
        if mime_type.startswith('image/'):
            url = entry['request']['url']
            image_urls.append(url)

# 下载图片
for i, url in enumerate(image_urls):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查是否请求成功
        # 生成文件名
        filename = os.path.join(download_folder, f'FileName{i}.jpg')
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"Download Success: {url}")
    except Exception as e:
        print(f"Download Failed: {url}, ERROR: {str(e)}")

print("Dowload Complete.")
