# sidecar/ocr/
"""
OCR local para imágenes y PDFs escaneados. Nada de este paquete se importa al arrancar el sidecar:
main.py lo importa bajo demanda para no cargar OpenCV/ONNX al convertir documentos o audio.
"""
