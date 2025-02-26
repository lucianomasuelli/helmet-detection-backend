import cv2
import torch
import asyncio
import websockets
from ultralytics import YOLO

# Cargar el modelo YOLOv8
model = YOLO("yolov8n.pt")  # Reemplazar con tu modelo entrenado

# URL del stream de video (o ruta del archivo)
video_path = '/home/luciano/Descargas/motorbikes.mp4'  # 0 para webcam, o 'ruta/al/video.mp4' para un video

async def detect_and_stream(websocket):
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Realizar la detección
        results = model(frame)

        # Contadores de detección
        motorcycle_count = 0
        helmet_count = 0

        # Procesar detecciones
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

        # Enviar datos al frontend en formato JSON
        await websocket.send(str({"motorcycles": motorcycle_count, "helmets": helmet_count}))

    cap.release()

async def websocket_server():
    async with websockets.serve(detect_and_stream, "localhost", 8001):
        await asyncio.Future()  # Mantiene el servidor en ejecución

if __name__ == "__main__":
    asyncio.run(websocket_server())
