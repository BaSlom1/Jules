import os
import time
import hashlib
import re

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} Б"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.2f} КБ"
    elif size_bytes < 1024**3:
        return f"{size_bytes / 1024**2:.2f} МБ"
    else:
        return f"{size_bytes / 1024**3:.2f} ГБ"

def get_directory_size_and_top_files(dir_path, top_n=5):
    total_size = 0
    files_list = []

    try:
        for dirpath, _, filenames in os.walk(dir_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    try:
                        size = os.path.getsize(fp)
                        total_size += size
                        files_list.append((f, size))
                    except Exception:
                        pass
    except Exception:
        pass

    # Sort files by size, descending
    files_list.sort(key=lambda x: x[1], reverse=True)
    top_files = files_list[:top_n]

    return total_size, top_files

def get_pe_metadata(filepath):
    try:
        import pefile
    except ImportError:
        return {}

    metadata = {}
    try:
        pe = pefile.PE(filepath)
        if hasattr(pe, 'VS_VERSIONINFO') and hasattr(pe, 'FileInfo'):
            for fileinfo in pe.FileInfo:
                for stringtable in fileinfo[0].StringTable:
                    for entry in stringtable.entries.items():
                        key = entry[0].decode('utf-8', errors='ignore')
                        value = entry[1].decode('utf-8', errors='ignore')
                        metadata[key] = value
    except Exception:
        pass
    return metadata

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def clean_path_for_query(path):
    # Remove user-specific parts (e.g. C:\Users\Username\)
    clean = re.sub(r"^[a-zA-Z]:\\Users\\[^\\]+\\", "", path)
    # Convert slashes to spaces
    clean = clean.replace('\\', ' ')
    clean = clean.replace('/', ' ')

    # Split to words, take parent folder and item name
    parts = clean.split()
    if len(parts) >= 2:
        return f"{parts[-2]} {parts[-1]}"
    elif len(parts) == 1:
        return parts[0]
    return ""

def generate_search_query(target_path, is_dir):
    basename = os.path.basename(target_path)

    context = clean_path_for_query(target_path)

    if is_dir:
        query = f'"{basename}" {context} что за папка OR "what is"'
    else:
        query = f'"{basename}" {context} что за программа файл OR "what is"'

    return query

def analyze_path(target_path):
    if not os.path.exists(target_path):
        return {"error": "Path does not exist"}

    is_dir = os.path.isdir(target_path)
    stat = os.stat(target_path)

    creation_time = stat.st_ctime
    mod_time = stat.st_mtime
    now = time.time()

    days_since_mod = int((now - mod_time) / (3600 * 24))

    # Format dates
    create_date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(creation_time))

    result = {
        "name": os.path.basename(target_path),
        "is_dir": is_dir,
        "days_since_mod": days_since_mod,
        "creation_date": create_date_str,
        "search_query": generate_search_query(target_path, is_dir)
    }

    if is_dir:
        size, top_files = get_directory_size_and_top_files(target_path)
        result["size"] = format_size(size)
        result["top_files"] = [{"name": f[0], "size": format_size(f[1])} for f in top_files]
    else:
        result["size"] = format_size(stat.st_size)

        # Check if it's an executable or DLL
        ext = os.path.splitext(target_path)[1].lower()
        if ext in ['.exe', '.dll']:
            result["pe_metadata"] = get_pe_metadata(target_path)

        # Calculate SHA-256 for VirusTotal
        result["sha256"] = calculate_sha256(target_path)

    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        print(analyze_path(sys.argv[1]))
