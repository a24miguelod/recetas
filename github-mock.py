import os
import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse

HOST = "192.168.1.138"
PORT = 8000
# Para simular retardo. Esperare una media de milisegundos, aleatorizados
# alrededor de este valor
SLEEP_TIME = 300

def json_ls(directorio):
    result = []
    dir = os.path.join(".", directorio)
    for file in os.listdir(dir):
        full_path = os.path.join(dir, file) 
        if file.endswith(".md") and os.path.isfile(full_path):
            entry = {
                "name": file,
                "download_url": f"http://{HOST}:{PORT}/recetas/{file}"
            }
            result.append(entry)
        else:
            print(f"Me salto {file}")
    return result

def normaliza(path):
    normalizado = os.path.normpath(path)
    if ".." in normalizado:
        raise Exception(f"Esto no debe ocurrir nunca: path {normalizado}")
    return os.path.join(".", normalizado)

def sleep_random_time():
    mitad = int(SLEEP_TIME / 2)
    aleatorio = random.randint(SLEEP_TIME-mitad, SLEEP_TIME+mitad)
    print(f"Espero {aleatorio} ms")

    time.sleep(aleatorio/1000.0)


class SimpleHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        sleep_random_time()
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        print(f"Llega {path}")

        # si la entrada es el raiz, simulo la api de github
        if path == "/":
            print("Sirvo fichero")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = json_ls("recetas/")
            self.wfile.write(json.dumps(response, indent=2).encode("utf-8"))

        # si la entrada es un /recetas/ devuelvo el fichero .md en la carpeta recetas
        elif path.startswith("/recetas/"):
            full_path = normaliza(path[1:])
            print("Llamo con full path", full_path)

            if os.path.exists(full_path) and os.path.isfile(full_path):
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Disposition", "inline")
                self.end_headers()
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    self.wfile.write(f.read().encode("utf-8"))
            else:
                self.send_error(404, "File not found")

            # Carpeta de fotos
        elif path.startswith("/fotos/"):
            filename = path[len("/fotos/"):]
            if ".." in filename or "/" in filename:
                self.send_error(400, "Invalid path")
                return
        
            image_path = os.path.join("fotos", filename)
            print(f"imate_path: $filename, Recogo ${image_path}")
            if os.path.isfile(image_path):
                # Detectar MIME según extensión
                ext = os.path.splitext(filename)[1].lower()
                mime_types = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                    ".bmp": "image/bmp"
                }
                mime_type = mime_types.get(ext, "application/octet-stream")
        
                self.send_response(200)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Disposition", f"inline; filename=\"{filename}\"")
                self.end_headers()
                with open(image_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Image not found")
        else:
            self.send_error(404, "Path not found")
        

def run():
    print(f"Servidor escuchando en http://{HOST}:{PORT}/")
    server = HTTPServer((HOST, PORT), SimpleHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()
