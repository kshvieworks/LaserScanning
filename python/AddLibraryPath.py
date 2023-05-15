import os

# Setting folder paths: The thorlabs software must know where the dll's are located, so add them to the environ['PATH']

def configure_path():
    relative_path_to_dlls = os.sep + 'venv' + os.sep + 'Lib' + os.sep + 'site-packages' + os.sep + 'thorlabs_tsi_sdk' + os.sep + 'Native_64_lib'
    os.environ['PATH'] = os.getcwd() + relative_path_to_dlls + os.pathsep + os.environ['PATH']

    try:
        os.add_dll_directory(os.getcwd() + relative_path_to_dlls)
    # except AttributeError:
    except AttributeError or FileNotFoundError:
        pass

    del relative_path_to_dlls
