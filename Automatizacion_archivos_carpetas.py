# Desde paso 2 al 3 creamos las carpetas de la ruta (paso1), en el caso de que no existan y las ordenamos.
# En el paso 5 creamos un bucle por archivo que cada tipo de archivo se crea una carpeta y se ordena el archivo en la carpeta correspondiente

import os
import shutil

# 1. Ruta donde estan los archivos y carpetas que queremos ordenar
ruta = "G:/Mi unidad/DAW/4 SEMESTRE/PROYECTO/PROYECTO 2024/PROYECTO MyR"


# 2. Lista de las carpetas que queremos ordenar
tipos=["EXCEL", "WORD", "DRAWIO", "VIDEOS", "TXTS"]

# 3. Recorremos la lista de las carpetas y las creamos sino existen
for carpeta in tipos:
    
    ruta_carpeta = os.path.join(ruta, carpeta)
    
    # Si no existe la carpeta
    if not os.path.exists(ruta_carpeta):
        
        # la creamos
        os.makedirs(ruta_carpeta)
        print(f"La carpeta {carpeta} ha sido creada")
    else:
        print(f"La carpeta {carpeta} ya existe")


# 4. Para cada archivo en la ruta que hemos definido
for archivo in os.listdir(ruta):
    
    # Si el archivo termina en .txt
    if archivo.endswith(".txt"):
        # Movemos el archivo a la carpeta TXTS
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "TXTS", archivo))
        
        print(f"El archivo {archivo} ha sido movido a la carpeta TXTS")
        
    # Si el archivo termina en .docx
    elif archivo.endswith(".docx"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "WORD", archivo))
        
        print(f"El archivo {archivo} ha sido movido a la carpeta WORD")
        
    # Si el archivo termina en .xlsx
    elif archivo.endswith(".xlsx"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "EXCEL", archivo))
        
        print(f"El archivo {archivo} ha sido movido a la carpeta EXCEL")
        
    # Si el archivo termina en .drawio
    elif archivo.endswith(".drawio"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "DRAWIO", archivo))
        
        print(f"El archivo {archivo} ha sido movido a la carpeta DRAWIO")
        
    # Si el archivo termina en .mp4
    elif archivo.endswith(".mp4"):
        shutil.move(os.path.join(ruta, archivo), os.path.join(ruta, "VIDEOS", archivo))
        
        print(f"El archivo {archivo} ha sido movido a la carpeta VIDEOS")
        
# 6. Ordenamos las carpetas alfabeticamente
carpetas_en_ruta = [nombre for nombre in os.listdir(ruta) if os.path.isdir(os.path.join(ruta, nombre))]
carpetas_en_ruta.sort()
        
        
        