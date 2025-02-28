import asyncio
import cv2
import sys
from ultralytics import YOLO
import yt_dlp

model = YOLO("yolov8n.pt")

def get_video_stream_url(youtube_url):
    # Gets the direct stream URL using yt-dlp from YouTube link
    ydl_opts = {
        "format": "best[ext=mp4]",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return info["url"] if "url" in info else None

async def detect(video_url):
    # Obtains the video stream URL if the input is a YouTube link
    if "youtube.com" in video_url or "youtu.be" in video_url:
        video_url = get_video_stream_url(video_url)
        if not video_url:
            print("Error: Cannot get video stream URL from YouTube link.")
            return

    cap = cv2.VideoCapture(video_url)

    motorcycle_count = 0
    helmet_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Perform inference
        results = model(frame)

        # Count the number of motorcycles and helmets detected
        for result in results:
            for box in result.boxes:
                label = model.names[int(box.cls)]
                if label == "motorcycle":
                    motorcycle_count += 1
                elif label == "helmet":
                    helmet_count += 1

        # Visualize the results on the frame
        annotated_frame = results[0].plot()

        # Display the annotated frame
        cv2.imshow("YOLO Inference", annotated_frame)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # Send the detection counts to the server
        print(str({"motorcycles": motorcycle_count, "helmets": helmet_count}))

    cap.release()

async def main():
    video_url = sys.argv[1]
    print(f"Procesando video: {video_url}")
    await detect(video_url)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: No se proporcionó una URL de video.")
        sys.exit(1)

    asyncio.run(main())
