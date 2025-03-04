import asyncio
import cv2
import sys
import json
from ultralytics import YOLO
import yt_dlp
import websockets

model = YOLO("yolov8n.pt")

# gets the video stream URL from a YouTube link
def get_video_stream_url(youtube_url):
    ydl_opts = {
        "format": "best[ext=mp4]",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"] if "url" in info else None


async def detect(video_url, websocket):
    if "youtube.com" in video_url or "youtu.be" in video_url:
        video_url = get_video_stream_url(video_url)
        if not video_url:
            print("Error: Cannot get video stream URL from YouTube link.")
            return

    cap = cv2.VideoCapture(video_url)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)

        motorcycle_count = 0
        helmet_count = 0
        for result in results:
            for box in result.boxes:
                label = model.names[int(box.cls)]
                if label == "motorcycle":
                    motorcycle_count += 1
                elif label == "helmet":
                    helmet_count += 1

        annotated_frame = results[0].plot()
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        frame_bytes = buffer.tobytes()

        data = {
            "motorcycles": motorcycle_count,
            "helmets": helmet_count,
            "frame": frame_bytes.hex()
        }
        await websocket.send(json.dumps(data))

    cap.release()


async def websocket_server():
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

async def handler(websocket):
    async for video_url in websocket:
        print(f"Procesando video: {video_url}")
        await detect(video_url, websocket)

if __name__ == "__main__":
    asyncio.run(websocket_server())