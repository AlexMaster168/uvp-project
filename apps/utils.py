import unicodedata
import os


_CYR_TO_LAT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e',
    'ё': 'yo', 'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',
    'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r',
    'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts',
    'ч': 'ch', 'ш': 'sh', 'щ': 'shch', 'ъ': '', 'ы': 'y', 'ь': '',
    'э': 'e', 'ю': 'yu', 'я': 'ya',
}

_CYR_TO_LAT.update({k.upper(): v.capitalize() for k, v in list(_CYR_TO_LAT.items()) if v})


def transliterate(text):
    result = []
    for char in text:
        if char in _CYR_TO_LAT:
            result.append(_CYR_TO_LAT[char])
        elif unicodedata.category(char).startswith('L'):
            result.append(char)
        elif char in (' ', '-', '_', '.'):
            result.append('_')
        elif char.isdigit():
            result.append(char)
    return ''.join(result)


def translit_upload_to(subdir):
    def handler(instance, filename):
        name, ext = os.path.splitext(filename)
        safe_name = transliterate(name) + ext.lower()
        return f'{subdir}/{safe_name}'
    return handler
