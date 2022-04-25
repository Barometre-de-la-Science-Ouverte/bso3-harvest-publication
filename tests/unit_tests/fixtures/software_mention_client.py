import json
import os


class software_mentions_client:
    def __init__(self, config_path, *args, **kwargs):
        pass

    def annotate_directory(self, directory, *args, **kwargs):
        out_files = []
        for root, directories, filenames in os.walk(directory):
            for filename in filenames:
                print(filename)
                if (filename.endswith(".pdf") or filename.endswith(".PDF") or filename.endswith(".pdf.gz")):
                    if filename.endswith(".pdf"):
                        filename_json = filename.replace(".pdf", ".software.json")
                    elif filename.endswith(".pdf.gz"):
                        filename_json = filename.replace(".pdf.gz", ".software.json")
                    elif filename.endswith(".PDF"):
                        filename_json = filename.replace(".PDF", ".software.json")
                    out_files.append(os.path.join(root, filename_json))
        print('out_files', out_files)
        for out_file in out_files:
            with open(out_file, "w", encoding="utf-8") as json_file:
                json_file.write(json.dumps({"version": "1"}))
            print('out_file', out_file, 'exists', os.path.exists(out_file))

    def diagnostic(self, *args, **kwargs):
        pass
