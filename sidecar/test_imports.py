try:
    import pptx
    print('pptx OK:', pptx.__version__)
except Exception as e:
    print('pptx FALLO:', e)
try:
    import lxml
    print('lxml OK')
except Exception as e:
    print('lxml FALLO:', e)
try:
    from PIL import Image
    print('PIL OK')
except Exception as e:
    print('PIL FALLO:', e)
