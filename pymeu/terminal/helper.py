import pycomm3
import struct
from warnings import warn

from .paths import *

from ..constants import *
from ..messages import *
from ..types import *

def run_function(cip: pycomm3.CIPDriver, req_args):
    req_data = b''.join(arg.encode() + b'\x00' for arg in req_args)

    # Response format
    #
    # Byte 0 to 3 response code (typically 0 = function ran, otherwise failed, not all functions follow this)
    # Byte 4 to N-1 response data
    # Byte N null footer
    resp = msg_run_function(cip, req_data)
    if not resp: raise Exception(f'Failed to run function: {req_args}.')
    resp_code = int.from_bytes(resp.value[:4], byteorder='little', signed=False)
    resp_data = resp.value[4:].decode('utf-8').strip('\x00')
    return resp_code, resp_data

def create_directory(cip: pycomm3.CIPDriver, dir: str) -> bool:
    req_args = [helper_file_path, 'CreateRemDirectory', dir]
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != CREATE_DIR_SUCCESS): raise Exception('Failed to create directory on terminal.')    
    return True

def create_mer_list(cip: pycomm3.CIPDriver):
    req_args = [helper_file_path,'FileBrowse',storage_path + '\\Rockwell Software\\RSViewME\\Runtime\\*.mer::' + storage_path + UPLOAD_LIST_PATH]
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Response code was not zero.  Examine packets.')
    return True

def create_runtime_directory(cip: pycomm3.CIPDriver, file: MEFile) -> bool:
    # Create paths
    if not(create_directory(cip, storage_path)): return False
    if not(create_directory(cip, storage_path + '\\Rockwell Software')): return False
    if not(create_directory(cip, storage_path + '\\Rockwell Software\\RSViewME')): return False
    if not(create_directory(cip, storage_path + '\\Rockwell Software\\RSViewME\\Runtime')): return False
    return True

def delete_file(cip: pycomm3.CIPDriver, file: str) -> bool:
    req_args = [helper_file_path,'DeleteRemFile',file]
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Failed to delete file on remote terminal {file}')
    return True

def delete_file_mer_list(cip: pycomm3.CIPDriver) -> bool:
    return delete_file(cip, storage_path + UPLOAD_LIST_PATH)

def get_file_exists(cip: pycomm3.CIPDriver, file: MEFile) -> bool:
    req_args = [helper_file_path, 'FileExists', storage_path + f'\\Rockwell Software\\RSViewME\\Runtime\\{file.name}']
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): return False    
    return bool(int(resp_data))

def get_file_size(cip: pycomm3.CIPDriver, file: MEFile) -> int:
    req_args = [helper_file_path, 'FileSize', storage_path + f'\\Rockwell Software\\RSViewME\\Runtime\\{file.name}']
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Response code was not zero.  Examine packets.')
    return int(resp_data)

def get_folder_exists(cip: pycomm3.CIPDriver) -> bool:
    req_args = [helper_file_path, 'StorageExists', storage_path]
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0):
        warn(f'Response code was not zero.  Examine packets.')
        return False
    return bool(int(resp_data))

def get_free_space(cip: pycomm3.CIPDriver) -> int:
    req_args = [helper_file_path, 'FreeSpace', storage_path + '\\Rockwell Software\\RSViewME\\Runtime\\']
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Response code was not zero.  Examine packets.')
    return int(resp_data)

def get_helper_version(cip: pycomm3.CIPDriver) -> str:
    req_args = [helper_file_path, 'GetVersion', helper_file_path]
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Response code was not zero.  Examine packets.')
    return str(resp_data)

def reboot(cip: pycomm3.CIPDriver):
    # For some reason this one has an extra trailing byte.
    # Not sure if it has some other purpose yet
    req_args = [helper_file_path, 'BootTerminal','']
    req_data = b''.join(arg.encode() + b'\x00' for arg in req_args)

    try:
        resp = msg_run_function(cip, req_data)
        
        #Should never get here
        raise Exception(resp)
    except pycomm3.exceptions.CommError as e:
        # Unlike most CIP messages, this one is always expected to
        # create an exception.  When it is received by the terminal,
        # the device reboots and breaks the socket.
        if (str(e) != 'failed to receive reply'): raise e

def set_startup_mer(cip: pycomm3.CIPDriver, file: MEFile, replace_comms: bool, delete_logs: bool) -> bool:
    req_args = [helper_file_path, 'CreateRemMEStartupShortcut', storage_path + f':{file.name}: /r /delay']
    if replace_comms: req_args = [req_args[1], req_args[2], req_args[3] + ' /o']
    if delete_logs: req_args = [req_args[1], req_args[2], req_args[3] + ' /d']
    resp_code, resp_data = run_function(cip, req_args)
    if (resp_code != 0): raise Exception(f'Response code was not zero.  Examine packets.')
    return True