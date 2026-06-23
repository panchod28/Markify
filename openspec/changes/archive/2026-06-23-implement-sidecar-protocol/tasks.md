## 1. Protocol Layer

- [x] 1.1 Create `sidecar/protocol.py` with `read_message()` and `write_message()` functions

## 2. Error Messages

- [x] 2.1 Create `sidecar/error_messages.py` with bilingual ES/EN error map and `get_error_message()` function

## 3. Sanitizer

- [x] 3.1 Create `sidecar/sanitizer.py` with `sanitize_filename()` using unicodedata NFKD normalization

## 4. Document Converter

- [x] 4.1 Create `sidecar/converter.py` with MarkItDown singleton and `convert_document()` with validation and error handling

## 5. Whisper Handler

- [x] 5.1 Create `sidecar/whisper_handler.py` with `transcribe_audio()` supporting cancel flag, progress emission, and Markdown formatting

## 6. Model Manager

- [x] 6.1 Create `sidecar/model_manager.py` with `get_model_path()`, `model_exists()`, and `download_model()` with progress callback

## 7. Main Entry Point

- [x] 7.1 Create `sidecar/main.py` with stdin loop, command dispatch, `handle_convert()`, `handle_download_model()`, and cancel flag

## 8. Dependencies

- [x] 8.1 Create `sidecar/requirements.txt` with markitdown, openai-whisper, torch+cpu, and PyInstaller
