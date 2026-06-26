from PyInstaller.utils.hooks import copy_metadata, collect_all

datas = []
datas += copy_metadata('markitdown')
datas += copy_metadata('python-pptx')
datas += copy_metadata('openpyxl')
datas += copy_metadata('xlrd')
datas += copy_metadata('lxml')
datas += copy_metadata('Pillow')
