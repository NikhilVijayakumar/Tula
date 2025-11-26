import chardet
import os
import tempfile
import shutil

class Utf8Utils:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def convert_to_utf8(self):
        try:
            with open(self.file_path, 'rb') as f:
                raw_data = f.read()

            detected_info = chardet.detect(raw_data)
            current_encoding = detected_info.get('encoding')
            confidence = detected_info.get('confidence', 0.0)

            if not current_encoding or confidence < 0.8:
                print(f"⚠️ Warning: Could not reliably detect encoding for '{self.file_path}'. Confidence: {confidence:.2f}")
                print("   Falling back to latin-1.")
                current_encoding = 'latin-1'

            print(f"Detected encoding: {current_encoding} (confidence {confidence:.2f})")

            try:
                # Try decoding normally
                content = raw_data.decode(current_encoding)
            except UnicodeDecodeError:
                print(f"⚠️ Decode failed with {current_encoding}, retrying with errors='replace'...")
                try:
                    # Replace problematic characters with �
                    content = raw_data.decode(current_encoding, errors="replace")
                except Exception:
                    print("⚠️ Still failed, forcing latin-1 as last resort...")
                    content = raw_data.decode("latin-1", errors="replace")

            # Write safely to UTF-8
            tmp_fd, tmp_path = tempfile.mkstemp()
            with os.fdopen(tmp_fd, 'w', encoding='utf-8', newline='') as f:
                f.write(content)

            shutil.move(tmp_path, self.file_path)

            print(f"✅ File '{self.file_path}' successfully converted to UTF-8.")

        except Exception as e:
            print(f"❌ An error occurred during conversion: {e}")
