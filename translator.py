import yaml
import os

class Translator:
    def __init__(self, lang_dir="lang", subject_file="data/subjects.yaml"):
        self.lang_dir = lang_dir
        self.subject_file = subject_file
        self.translations = {}
        self.subject_actions = {}
        self.subject_cache = {} 
        self._load_translations()
        self._load_subjects()

    def _load_translations(self):
        for filename in os.listdir(self.lang_dir):
            if filename.endswith(".yaml"):
                lang_code = filename.split(".")[0]
                with open(os.path.join(self.lang_dir, filename), "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.translations[lang_code] = data

    def _load_subjects(self):
        print("Looking for subjects.yaml at:", self.subject_file)
        if os.path.exists(self.subject_file):
            with open(self.subject_file, "r", encoding="utf-8") as f:
                self.subject_actions = yaml.safe_load(f)
            print("✅ Subjects loaded:", list(self.subject_actions.keys()))
        else:
            print("❌ subjects.yaml not found!")


    def t(self, key, lang):
        return self.translations.get(lang, {}).get(key, key)

    def get_subject_options(self, subject):
        return self.subject_actions.get(subject, [])
