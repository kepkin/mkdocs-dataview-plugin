"""
Helper module to work with files.
"""
import os.path


def enumerate_files_by_ext(path, ext_list=None):
    """
    Generator for files filtered by extension
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            if ext_list is not None:
                _, extension = os.path.splitext(file)
                if extension in ext_list:
                    yield os.path.join(root, file)

        for dir_name in dirs:
            enumerate_files_by_ext(os.path.join(root, dir_name), ext_list)
