import os
import shutil
import tkinter as tk
import datetime
import getpass
import threading 

from tkinter import filedialog, messagebox
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Capturamos el usuario del sistema
usuario = getpass.getuser()

# Diccionario de categorías y sus tipos de carpetas con extensiones asociadas
CATEGORIAS = {
    "Ofimática": {
        "WORD": [".docx", ".doc"], "EXCEL": [".xlsx", ".xls"], "PPT": [".pptx", ".ppt"],
        "PDFS": [".pdf"], "DRAWIO": [".drawio"], "TXTS": [".txt"],
    },
    "Imágenes": {"IMAGENES": [".jpg", ".jpeg", ".png", ".svg", ".gif"]},
    "Audio": {"MP3": [".mp3"]},
    "Video": {"VIDEOS": [".mp4", ".avi", ".mov", ".mkv"]},
    "Comprimidos": {"ZIP": [".zip", ".rar", ".7z"]}
}

# Unifica todos los tipos en un solo diccionario. Facilita la busqueda de extensiones
TIPOS_CARPETAS = {}
for categoria_dict_loop in CATEGORIAS.values(): # Renombrada variable de bucle para evitar shadowing
    TIPOS_CARPETAS.update(categoria_dict_loop)

# --- Variables Globales para el Observador ---
observer = None # Variable global para el objeto Observer de watchdog
observer_thread = None # Variable global para el hilo del observador
ruta_observada_actualmente = None # Para saber qué carpeta se está observando

# --- FUNCION MOVER CARPETAS ---
# Modificada para aceptar argumentos opcionales para ser usada por watchdog
def organizar_carpeta(ruta_base_observada_param=None, archivo_especifico_param=None):
    
    global observer, observer_thread, ruta_observada_actualmente # Necesitamos acceder/modificar estas globales

    # Determinar la 'ruta' base de operación
    if ruta_base_observada_param:
        
        # Si watchdog llama a esta función, ruta_base_observada_param es la carpeta que se observa
        ruta = ruta_base_observada_param
        print(f"[Watchdog] organizar_carpeta llamada para ruta base: {ruta} y archivo: {archivo_especifico_param}")
        
    else:
        
        # Si el botón llama a esta función, pedimos la ruta al usuario
        ruta = filedialog.askdirectory(title="Selecciona la carpeta a organizar")
        
        if not ruta:
            return # El usuario canceló la selección
        
        print(f"[Botón GUI] organizar_carpeta llamada para organizar todo en: {ruta}")


    # Obtiene los tipos seleccionados por el usuario en los checkboxes (variable global 'checks' de la GUI)
    # Esta parte es común tanto para el botón como para watchdog (asume que los 'checks' reflejan la configuración deseada)
    tipos_seleccionados = [tipo for tipo, var_check in checks.items() if var_check.get()] # var_check para claridad

    if not tipos_seleccionados:
        
        if not ruta_base_observada_param: # Solo mostrar messagebox si fue el botón
            messagebox.showwarning("Advertencia", "Selecciona al menos un tipo de carpeta.")
            
        else:
            print("[Watchdog] No hay tipos de archivo seleccionados para organizar.")
            
        return

    # --- LOG ---
    log_filename = "log_organizador.txt"
    log_filepath = os.path.join(ruta, log_filename)
    archivos_movidos_contador = 0

    # --- LÓGICA DE PROCESAMIENTO ---
    archivos_a_procesar = []
    
    if archivo_especifico_param:
        # Caso Watchdog: solo procesar el archivo nuevo
        # archivo_especifico_param es la ruta completa del archivo.
        # Necesitamos asegurarnos de que el archivo todavía existe y está en la ruta base.
        
        if os.path.isfile(archivo_especifico_param) and os.path.dirname(archivo_especifico_param) == ruta:
            archivos_a_procesar = [os.path.basename(archivo_especifico_param)]
            
        else:
            print(f"[Watchdog] El archivo {archivo_especifico_param} ya no existe o no está en la carpeta raíz observada.")
            return # No procesar
        
    else:
        # Caso Botón GUI: procesar todos los archivos en la ruta
        try:
            
            archivos_a_procesar = os.listdir(ruta)
        except FileNotFoundError:
            
            messagebox.showerror("Error", f"La carpeta {ruta} no fue encontrada.")
            
            return

    # Iterar sobre los archivos determinados (sea uno o todos)
    for archivo_nombre in archivos_a_procesar:
        
        if archivo_nombre == log_filename:
            continue

        ruta_archivo_origen = os.path.join(ruta, archivo_nombre)

        if not os.path.isfile(ruta_archivo_origen): # Verificar si el archivo aún existe y es un archivo
            
            if archivo_especifico_param: # Si es de watchdog, puede haber sido movido/eliminado rápidamente
                
                print(f"[Watchdog] El archivo {ruta_archivo_origen} no se encontró o no es un archivo al momento de procesar.")
                
            continue # Saltar si no es un archivo (podría ser una carpeta creada o un archivo eliminado)

        for carpeta_destino_final in tipos_seleccionados:
            
            if any(archivo_nombre.lower().endswith(ext) for ext in TIPOS_CARPETAS[carpeta_destino_final]):
                
                try:
                    timestamp_modificacion = os.path.getmtime(ruta_archivo_origen)
                    fecha_modificacion_obj = datetime.datetime.fromtimestamp(timestamp_modificacion)
                    nombre_subcarpeta_fecha = fecha_modificacion_obj.strftime("%d-%m-%Y") # Formato DD-MM-YYYY

                    ruta_destino_con_fecha = os.path.join(ruta, carpeta_destino_final, nombre_subcarpeta_fecha)
                    os.makedirs(ruta_destino_con_fecha, exist_ok=True)
                    ruta_final_del_archivo = os.path.join(ruta_destino_con_fecha, archivo_nombre)

                    # Evitar mover si ya está en destino (más relevante para el escaneo completo)
                    if os.path.abspath(ruta_archivo_origen) == os.path.abspath(ruta_final_del_archivo):
                        continue

                    shutil.move(ruta_archivo_origen, ruta_final_del_archivo)

                    with open(log_filepath, "a", encoding="utf-8") as log_file:
                        timestamp_log_actual = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        prefijo_log = "[Auto]" if archivo_especifico_param else "[Manual]"
                        destino_para_log = os.path.join(carpeta_destino_final, nombre_subcarpeta_fecha)
                        log_entry = f"[{timestamp_log_actual}] {prefijo_log} Usuario: {usuario} - Movido: '{archivo_nombre}' -> '{destino_para_log}'\n"
                        log_file.write(log_entry)
                        
                    archivos_movidos_contador += 1
                    
                except FileNotFoundError:
                    
                    # El archivo pudo haber sido movido o eliminado entre listarlo y procesarlo.
                    print(f"Error (FileNotFound) procesando archivo {archivo_nombre}. Pudo haber sido movido o eliminado.")
                    
                    with open(log_filepath, "a", encoding="utf-8") as log_file_err:
                        ts_err = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_file_err.write(f"[{ts_err}] Usuario: {usuario} - ERROR (FileNotFound) al intentar mover '{archivo_nombre}'\n")
                        
                except Exception as e:
                    
                    print(f"Error procesando archivo {archivo_nombre}: {e}")
                    
                    with open(log_filepath, "a", encoding="utf-8") as log_file_err:
                        ts_err = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_file_err.write(f"[{ts_err}] Usuario: {usuario} - ERROR al mover '{archivo_nombre}': {e}\n")
                        
                break # Archivo procesado (o error manejado), pasar al siguiente archivo

    # --- Mostrar mensaje solo si fue llamado por el botón ---
    if not ruta_base_observada_param: # Es decir, si 'ruta' fue obtenida por filedialog
        
        if archivos_movidos_contador > 0:
            
            messagebox.showinfo("Organización Completada",
                                f"Se movieron {archivos_movidos_contador} archivo(s).\n"
                                f"El registro se guardó en: {log_filepath}")
            
        else:
            messagebox.showinfo("Sin cambios", "No se movió ningún archivo que coincidiera con los tipos seleccionados.")

        # --- INICIAR EL OBSERVADOR DESPUÉS DE LA ORGANIZACIÓN MANUAL ---
        
        if ruta: # Si se seleccionó una ruta válida
            
            if observer is not None: # Detener observador anterior si existe
                print("Deteniendo observador anterior...")
                observer.stop()
                
                if observer_thread is not None and observer_thread.is_alive():
                    
                    observer_thread.join() # Esperar a que el hilo termine
                    
                print("Observador anterior detenido.")

            print(f"Iniciando observador para la carpeta: {ruta}")
            event_handler = ManejadorEventos(ruta_observada=ruta) # Pasar la ruta al manejador
            observer = Observer()
            # recursive=False para observar solo la carpeta raíz, no subdirectorios creados por la organización.
            observer.schedule(event_handler, ruta, recursive=False)

            # Ejecutar el observador en un hilo separado
            observer_thread = threading.Thread(target=observer.start, daemon=True)
            observer_thread.start()
            ruta_observada_actualmente = ruta
            print(f"Observador iniciado en hilo para: {ruta_observada_actualmente}")

# Clase de EVENTOS
class ManejadorEventos(FileSystemEventHandler):
    
    def __init__(self, ruta_observada): # Constructor para recibir la ruta que se está observando
        
        super().__init__()
        self.ruta_observada_base = ruta_observada
        print(f"ManejadorEventos inicializado para observar: {self.ruta_observada_base}")

    def on_created(self, event):
        
        print(f"ManejadorEventos: Evento '{event.event_type}' detectado para: {event.src_path}")
        if not event.is_directory:
            
            # Llamamos a 'organizar_carpeta' pasando la ruta base observada y la ruta del archivo específico
            # Esto activará la lógica dentro de 'organizar_carpeta' para procesar solo este archivo.
            # Comprobamos que el archivo creado esté directamente en la carpeta observada
            if os.path.dirname(event.src_path) == self.ruta_observada_base:
                
                print(f"ManejadorEventos: Archivo creado en carpeta raíz: {event.src_path}. Llamando a organizar_carpeta.")
                # Llamada a la función 'organizar_carpeta' que ahora está definida globalmente y antes
                organizar_carpeta(ruta_base_observada_param=self.ruta_observada_base,
                    archivo_especifico_param=event.src_path)
                
            else:
                print(f"ManejadorEventos: Archivo creado en subcarpeta {os.path.dirname(event.src_path)}, ignorando.")


# --- INTERFAZ GRAFICA  ---
if __name__ == "__main__": # Para asegurar que la GUI se ejecute solo si es el script principal
    
    root = tk.Tk()
    root.title("ORGANIZADOR DE CARPETAS AUTOMÁTICO")
    
    try:
        root.iconbitmap("G:/Mi unidad/PROYECTOS/PTYHON/ORDENAR ARCHIVOS Y CARPETAS/carpeta.ico")
    except tk.TclError:
        
        print("Advertencia: No se pudo cargar el icono. Verifica la ruta o comenta la línea `root.iconbitmap`.")
        
    root.geometry("450x600")
    root.eval("tk::PlaceWindow . center")

    frame = tk.Frame(root)
    frame.pack(pady=10)

    checks = {} # Diccionario para almacenar el estado (activado o desactivado) de cada checkbutton

    tk.Label(frame, text="Selecciona los tipos de carpetas a organizar:", font=("Arial", 11, "bold")).pack(anchor="w", pady=(0,5))

    for categoria, tipos in CATEGORIAS.items():
        
        cat_label = tk.Label(frame, text=categoria, font=("Arial", 10, "bold"), fg="#2563eb")
        cat_label.pack(anchor="w", pady=(10,0))
        
        for tipo, extensiones in tipos.items():
            
            ext_text = ", ".join(extensiones)
            texto_check = f"{tipo} ({ext_text})"
            var = tk.BooleanVar(value=True) # 'var' es local al bucle, no hay conflicto
            chk = tk.Checkbutton(frame, text=texto_check, variable=var)
            chk.pack(anchor="w", padx=15)
            checks[tipo] = var # 'checks' es la variable global de la GUI

    # El botón ahora llama a 'organizar_carpeta' sin argumentos.
    # 'organizar_carpeta' manejará la selección de carpeta, la organización inicial Y el inicio del observador.
    
    btn_organizar = tk.Button(root, text="Seleccionar Carpeta, Organizar y Observar",
        command=organizar_carpeta, # Llama a la función 'organizar_carpeta' global
        bg="#3b82f6", fg="white", font=("Arial", 10, "bold"))
    
    btn_organizar.pack(padx=20, pady=30)

    def al_cerrar_ventana():
        
        global observer, observer_thread
        print("Cerrando aplicación...")
        
        if observer is not None and observer.is_alive():
            print("Deteniendo observador de archivos...")
            observer.stop()
            
            if observer_thread is not None and observer_thread.is_alive():
                observer_thread.join(timeout=2) # Esperar al hilo con un timeout
                
            print("Observador detenido.")
            
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", al_cerrar_ventana)
    root.mainloop()