from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import shutil
from ultralytics import YOLO
import os
from datetime import datetime
import atexit
import yt_dlp
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

# Middleware personalizado para logging
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Obtener información de la petición
        client_host = request.client.host if request.client else "Unknown"
        method = request.method
        url = request.url
        headers = request.headers
        
        # Imprimir información de la petición
        print(f"\n=== Nueva Petición ===")
        print(f"Cliente: {client_host}")
        print(f"Método: {method}")
        print(f"URL: {url}")
        print(f"Headers: {dict(headers)}")
        print("====================\n")
        
        # Continuar con la petición
        response = await call_next(request)
        return response

# Agregar el middleware de logging
app.add_middleware(LoggingMiddleware)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
    expose_headers=["*"]  
)
model = YOLO("best.pt")  # Cargar modelo YOLOv8 preentrenado

VIDEO_OUTPUT_DIR = "videos"
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)  # Crear directorio si no existe

class YouTubeURL(BaseModel):
    url: str

def download_youtube_video(url: str) -> str:
    """Descarga un video de YouTube y retorna la ruta del archivo"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"youtube_{timestamp}.mp4"
        output_path = os.path.join(VIDEO_OUTPUT_DIR, output_filename)
        
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': output_path,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        return output_path
    except Exception as e:
        print(f"Error al descargar video de YouTube: {e}")
        raise Exception(f"Error al descargar video de YouTube: {e}")

def cleanup_videos():
    """Limpia todos los archivos en la carpeta de videos"""
    try:
        for filename in os.listdir(VIDEO_OUTPUT_DIR):
            file_path = os.path.join(VIDEO_OUTPUT_DIR, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error al eliminar {file_path}: {e}")
        print("Carpeta de videos limpiada exitosamente")
    except Exception as e:
        print(f"Error al limpiar la carpeta de videos: {e}")

# Registrar la función de limpieza para que se ejecute al detener el servidor
atexit.register(cleanup_videos)

@app.post("/process-youtube/")
async def process_youtube_video(youtube_data: YouTubeURL):
    try:
        # Descargar el video de YouTube
        print(f"Descargando video de YouTube: {youtube_data.url}")
        input_path = download_youtube_video(youtube_data.url)
        
        # Crear nombre para el archivo procesado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"processed_youtube_{timestamp}.mp4"
        output_path = os.path.join(VIDEO_OUTPUT_DIR, output_filename)
        
        # Procesar el video
        print("Iniciando procesamiento del video...")
        process_video(input_path, output_path)
        
        # Eliminar el video original de YouTube
        if os.path.exists(input_path):
            os.remove(input_path)
            
        return {
            "video_url": f"/videos/{output_filename}",
            "filename": output_filename
        }
    except Exception as e:
        print(f"Error al procesar video de YouTube: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/")
async def upload_video(file: UploadFile = File(...)):
    try:
        print(f"\n=== Procesando Upload ===")
        print(f"Nombre del archivo: {file.filename}")
        print(f"Tipo de contenido: {file.content_type}")
        
        # Verificar que el archivo sea un video
        if not file.content_type.startswith('video/'):
            print("Error: El archivo no es un video")
            raise HTTPException(status_code=400, detail="El archivo debe ser un video")

        # Crear nombre único para el archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_filename = f"temp_{timestamp}_{file.filename}"
        output_filename = f"processed_{timestamp}_{file.filename}"
        
        print(f"Archivo temporal: {temp_filename}")
        print(f"Archivo de salida: {output_filename}")
        
        temp_video_path = os.path.join(VIDEO_OUTPUT_DIR, temp_filename)
        output_video_path = os.path.join(VIDEO_OUTPUT_DIR, output_filename)

        # Guardar el archivo temporal
        with open(temp_video_path, "wb") as temp_video:
            shutil.copyfileobj(file.file, temp_video)
        print("Archivo temporal guardado correctamente")

        # Procesar el video
        print("Iniciando procesamiento del video...")
        process_video(temp_video_path, output_video_path)
        print("Video procesado correctamente")

        # Eliminar el archivo temporal
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            print("Archivo temporal eliminado")

        print("=== Upload Completado ===\n")
        return {
            "video_url": f"/videos/{output_filename}",
            "filename": output_filename
        }
    except Exception as e:
        print(f"Error al procesar el video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/videos/{video_filename}")
async def get_video(video_filename: str):
    try:
        video_path = os.path.join(VIDEO_OUTPUT_DIR, video_filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video no encontrado")
            
        # Verificar que el archivo es accesible
        if not os.access(video_path, os.R_OK):
            raise HTTPException(status_code=403, detail="No se puede acceder al video")
            
        # Verificar que el archivo es un video válido
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise HTTPException(status_code=400, detail="El archivo no es un video válido")
        cap.release()
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=video_filename,
            headers={
                "Content-Disposition": f"attachment; filename={video_filename}"
            }
        )
    except Exception as e:
        print(f"Error al servir el video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_video(input_path, output_path):
    try:
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("No se pudo abrir el video de entrada")

        # Obtener propiedades del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        print(f"Procesando video: {fps}fps, {width}x{height}")

        # Usar codec MJPG para mejor compatibilidad en Docker
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        if not out.isOpened():
            raise Exception("No se pudo crear el video de salida")

        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame)
            
            # Dibujar detecciones en el frame
            annotated_frame = results[0].plot()
            
            # Guardar frame procesado
            out.write(annotated_frame)
            frame_count += 1
            
            if frame_count % 100 == 0:
                print(f"Frames procesados: {frame_count}")

        print(f"Procesamiento completado. Total frames: {frame_count}")
        
    except Exception as e:
        print(f"Error en process_video: {str(e)}")
        raise
    finally:
        if 'cap' in locals():
            cap.release()
        if 'out' in locals():
            out.release()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)