import os


class GrobidClient:
    def __init__(self, config_path, *args, **kwargs):
        pass

    def process(self, service, input_path, *args, **kwargs):
        input_files = []
        for (dirpath, dirnames, filenames) in os.walk(input_path):
            for filename in filenames:
                if filename.endswith(".pdf") or filename.endswith(".PDF") or filename.endswith(".pdf.gz"):
                    input_files.append(os.path.join(dirpath, filename))
        print('input_files', input_files)
        for input_file in input_files:
            filename = self._output_file_name(input_file)
            try:
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "w", encoding="utf8") as tei_file:
                    tei_file.write("")
                print('filename', filename, 'exists', os.path.exists(filename))
                print()
            except OSError:
                print("Writing resulting TEI XML file", filename, "failed")

    def _output_file_name(self, input_file):
        return input_file.rstrip(".gz").rstrip(".pdf").rstrip(".PDF") + ".tei.xml"
