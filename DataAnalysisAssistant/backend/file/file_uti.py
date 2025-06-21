import json
import os
from typing import Optional, Dict, Union
from pathlib import Path
from others.const import USERS_ZONE_ROOT_PATH, UPLOADED_FILES_ROOT_PATH, CURRENT_HANDLING_FILE_FOLDER_NAME
import base64
import shutil
import tempfile

def format_file_tree(tree_dict, indent=0, empty_indent=0):
    """
    将文件树字典格式化为字符串表示

    Args:
        tree_dict: 文件树字典
        indent: 当前缩进级别

    Returns:
        str: 格式化后的文件树字符串
    """
    result = []
    indent_str = "    " * empty_indent
    indent_str += "|   " * indent

    for key, value in tree_dict.items():
        if isinstance(value, dict) and value:  # 如果是非空字典，表示是目录
            result.append(f"{indent_str}{key}{{")
            result.append(format_file_tree(value, indent + 1, empty_indent))
            result.append(f"{indent_str}}}")
        else:  # 文件
            result.append(f"{indent_str}{key}")

    return "\n".join(result)



def create_file_structure(base_path: Union[str, Path], file_tree: Dict) -> None:
    """
    根据文件树结构在指定路径下创建空文件和目录

    Args:
        base_path: 基础路径（在此路径下创建结构）
        file_tree: 文件树字典结构

    Example:
        create_file_structure("/tmp/project", current_handling_file_tree)
    """
    base_path = Path(base_path)
    print("create_file_structure "*3)
    def _create_structure(current_path: Path, tree_node: Dict):
        for name, content in tree_node.items():
            new_path = current_path / name

            if not "." in name:  # 目录
                new_path.mkdir(parents=True, exist_ok=True)
                _create_structure(new_path, content)
            else:  # 空字典视为文件
                new_path.parent.mkdir(parents=True, exist_ok=True)
                new_path.touch()  # 创建空文件

    _create_structure(base_path, file_tree)
    print(f"文件结构已在 {base_path} 下创建成功")

def get_user_work_zone_path(user_session:Union[Dict, str], end_slash=False):
    if isinstance(user_session, dict):
        wzp = USERS_ZONE_ROOT_PATH + "\\" + user_session["client_id"] + "\\" + CURRENT_HANDLING_FILE_FOLDER_NAME
    if isinstance(user_session, str):
        wzp = USERS_ZONE_ROOT_PATH + "\\" + user_session + "\\" + CURRENT_HANDLING_FILE_FOLDER_NAME
    if end_slash:
        return wzp + "\\"
    return wzp

def get_file_info(user_session):
    user_tree = user_session["current_handling_file_tree"]
    if user_tree is None:
        return None

    return get_user_work_zone_path(user_session) + "下的:\n\n" + format_file_tree(user_tree, 0, 1)

# 发送文件树--------------------------------------------------------------------------------------------------------------
def read_file_tree(client_id):
    """读取真实文件系统并返回树形结构"""
    root_path = get_user_work_zone_path(user_session=client_id)
    tree = {}
    tree[CURRENT_HANDLING_FILE_FOLDER_NAME] = _read_file_tree(root_path)
    return tree

def _read_file_tree(root_path):

    tree = {}

    for entry in os.listdir(root_path):
        full_path = os.path.join(root_path, entry)

        if os.path.isdir(full_path):
            # 递归读取子目录
            tree[entry] = _read_file_tree(full_path)
        else:
            # 文件节点用空字典表示
            tree[entry] = {}

    return tree

# 文件移动----------------------------------------------------------------------------------------------------------------
def get_path_spit_point(path:str, ignore_last_slash:bool=False)->int:
    """
    :param path: 以/分隔的路径
    :param ignore_last_slash: 是否忽略末端的/
    :return: 从后往前数的第一个斜杠的位置
    """
    i = len(path) - 1
    if ignore_last_slash:
        while i >= 0:
            if path[i] != "/":
                break
            i -= 1
    while i>=0:
        if path[i] == "/":
            break
        i -= 1
    return i

def to_real_path(virtual_path, user_session):

    if virtual_path[:5] == "tree/":
        real_root = USERS_ZONE_ROOT_PATH + "\\" + user_session["client_id"]
    elif virtual_path[:5] == "expl/":
        real_root = UPLOADED_FILES_ROOT_PATH
    else:
        return ""
    virtual_path = virtual_path[5:]
    return os.path.join(real_root, *virtual_path.split('/'))

async def handle_file_move(websocket, data, user_session):
    """处理真实文件移动操作"""
    try:
        from_path = data['from']  # 例如 "tree/main.py" 或 "expl/others/backup/"
        to_path = data['to']  # 例如 "tree/others/" 或 "expl/resource/"

        # 转换前端路径为真实文件系统路径


        real_from = to_real_path(from_path, user_session)
        real_to_dir = to_real_path(to_path, user_session)

        # 验证源文件/目录是否存在
        if not os.path.exists(real_from):
            raise FileNotFoundError(f"源路径不存在: {real_from}")

        # 验证目标是否是目录
        if not os.path.isdir(real_to_dir):
            raise NotADirectoryError(f"目标必须是目录: {real_to_dir}")

        # 获取文件名/目录名
        item_name = os.path.basename(real_from)
        real_to = os.path.join(real_to_dir, item_name)

        # 检查是否尝试移动目录到自身子目录
        if os.path.isdir(real_from) and real_to.startswith(real_from + os.sep):
            raise ValueError("不能移动目录到自身子目录")

        # 执行移动操作
        shutil.move(real_from, real_to)

        print(f"文件移动成功: {real_from} -> {real_to}")

        current_file_selection = user_session["current_file_selection"]
        if current_file_selection is not None:
            split_ppint = get_path_spit_point(from_path,ignore_last_slash=True) + 1
            current_file_selection_root_path = current_file_selection[ :split_ppint ]
            current_file_selection_item_name = current_file_selection[ split_ppint: ]
            '''print("move "*5)
            print(f"current_file_selection_root_path: {current_file_selection_root_path}")
            print(f"current_file_selection_item_name: {current_file_selection_item_name}")
            print(f"from_path: {from_path},from_path_root_path: {from_path[ :split_ppint ]}")
            print(f"to_path: {to_path}")'''
            if current_file_selection_root_path == from_path[ :split_ppint ]:
                user_session["current_file_selection"] = to_path + current_file_selection_item_name

    except Exception as e:
        print(f"文件移动失败: {e}")
        await websocket.send(json.dumps({
            "type": "file-move-result",
            "success": False,
            "error": str(e),
            "originalPath": data.get('from'),
            "newPath": data.get('to')
        }))


# 发送文件---------------------------------------------------------------------------------------------------------------

async def send_file(websocket, file_path):
    print("p "*40)
    print(file_path)
    # 如果是文件夹，先压缩它
    if os.path.isdir(file_path):
        # 获取文件夹的基本名称（不带路径的最后一部分）
        folder_name = os.path.basename(file_path.rstrip('\\'))
        # 创建一个临时文件来存储压缩包
        temp_dir = tempfile.mkdtemp()
        try:
            # 使用原始文件夹名称作为压缩包名称
            zip_filename = f"{folder_name}.zip"
            zip_path = os.path.join(temp_dir, zip_filename)

            # 创建压缩文件（注意：make_archive会自动添加扩展名）
            shutil.make_archive(os.path.join(temp_dir, folder_name), 'zip', file_path)

            # 递归调用自己发送压缩文件，保持原始文件夹名称
            await send_file(websocket, zip_path)
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir)
        return
    # 如果是文件，正常发送
    name = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(8192)  # 8KB/块
            if not chunk:
                break
            # 将数据块转换为 Base64 编码
            base64_chunk = base64.b64encode(chunk).decode('utf-8')
            await websocket.send(json.dumps({
                "type": "file-chunk",
                "fileName": name,
                "chunk": base64_chunk,
                "isLastChunk": not bool(f.peek(1))  # 检查是否是最后一个数据块
            }))

def rename_file_or_dir(old_path, new_name):
    # 生成新的路径
    dir_name = os.path.dirname(old_path.rstrip('\\'))
    new_path = os.path.join(dir_name, new_name)
    print(new_path)
    try:
        # 检查目标路径是否已存在
        if os.path.exists(new_path):
            return False, "目标路径已存在"

        # 如果是文件，使用 os.rename
        if os.path.isfile(old_path):
            os.rename(old_path, new_path)
        # 如果是文件夹，也可以用 os.rename，但推荐用 shutil.move（跨设备也能用）
        elif os.path.isdir(old_path):
            shutil.move(old_path, new_path)
        else:
            return False, "路径不存在或不是文件/文件夹"

        return True, "重命名成功"
    except Exception as e:
        return False, f"重命名失败: {e}"

def create_directory(dir_path):
    try:
        os.makedirs(dir_path, exist_ok=True)  # `exist_ok=True` 防止目录已存在时报错
        return True, "文件夹创建成功"
    except Exception as e:
        return False, f"文件夹创建失败: {e}"

async def update_display(websocket, user_session, envolved_files):
    all_prefix = [p[:5] for p in envolved_files]
    if "tree/" in all_prefix:
        await websocket.send(json.dumps({
            "type": "file-display_tree",
            "tree": read_file_tree(user_session["client_id"])
        }))
    if "expl/" in all_prefix:
        rp = to_real_path(user_session["current_viewing_directory"], user_session)
        if len(rp) > 0:
            await websocket.send(json.dumps({
                "type": "file-display_expl",
                "root": rp,
                "items": os.listdir(rp)
            }))

def get_tree_str(path):
    return format_file_tree(_read_file_tree(path))

if __name__ == "__main__":
    print(get_tree_str(r"C:\Users\chenghao\Qlib_LCH\qlib_related\qlib_pkg_shell\qlib"))