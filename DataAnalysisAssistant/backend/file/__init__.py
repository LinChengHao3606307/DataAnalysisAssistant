"""
user_sessions[websocket] = {
    "client_id": get_websocket_identifier(websocket),
    "active": False,
    "history": History(),
    "current_uploading_file": None,
    "current_handling_file_tree": None,
    "current_viewing_directory": None,
    "current_file_selection":None
}
"""
import json
import os
import shutil

from backend.file.file_uti import send_file, to_real_path, handle_file_move, rename_file_or_dir, update_display, \
    get_user_work_zone_path, create_directory, get_path_spit_point


async def handle_file_message(websocket, data, user_session):
    """处理所有文件相关操作"""
    if data["type"] == "file-upload-start":
        file_path = get_user_work_zone_path(user_session, end_slash=True) + data['name']
        user_session["current_uploading_file"] = open(file_path, 'wb')

    elif data["type"] == "file-upload-end":
        user_session["current_uploading_file"].close()
        await websocket.send(json.dumps({"type": "file-upload-end"}))
        await update_display(websocket, user_session,["tree/"])

    elif data["type"] == "file-download":
        real_file_path = to_real_path(data['path'], user_session)
        await send_file(websocket, real_file_path)

    elif data.get("type") == "file-delete":
        assert data['path'] == user_session["current_file_selection"]
        real_file_path = to_real_path(data['path'], user_session).rstrip('\\')
        try:
            if os.path.isfile(real_file_path):
                # 删除文件
                os.remove(real_file_path)
            elif os.path.isdir(real_file_path):
                # 删除文件夹（包括非空文件夹）
                shutil.rmtree(real_file_path)
            else:
                print(f"路径不存在: {real_file_path}")
        except PermissionError as e:
            print(f"权限不足，无法删除: {real_file_path}")
            print(f"错误详情: {e}")
        except Exception as e:
            print(f"删除时发生错误: {e}")
        await websocket.send(json.dumps({
            "type": "file-current-selection",
            "id": user_session["current_file_selection"],
            "action": "unselected"
        }))
        user_session["current_file_selection"] = None
        await update_display(websocket, user_session,[data['path']])

    elif data.get("type") == "file-move":
        await handle_file_move(websocket, data, user_session)
        await update_display(websocket, user_session,[data['from'],data['to']])
        if user_session["current_file_selection"]:
            print("= " * 50)
            await websocket.send(json.dumps({
                "type": "file-current-selection",
                "id": user_session["current_file_selection"],
                "action": "selected"
            }))

        # 文件选择请求
    if data.get("type") == "file-choose":
        user_session["current_file_selection"] = data["id"]
        await websocket.send(json.dumps({
            "type": "file-current-selection",
            "id": user_session["current_file_selection"],
            "action": "selected"
        }))

        # 文件取消选择请求
    elif data.get("type") == "file-unchoose":
        if user_session["current_file_selection"] == data["id"]:
            await websocket.send(json.dumps({
                "type": "file-current-selection",
                "id": user_session["current_file_selection"],
                "action": "unselected"
            }))
            user_session["current_file_selection"] = None

    elif data.get("type") == "file-rename":
        real_file_path = to_real_path(user_session["current_file_selection"], user_session)
        rename_file_or_dir(real_file_path, data["name"])
        await update_display(websocket, user_session,[user_session["current_file_selection"]])

    elif data.get("type") == "file-create":
        real_file_path = get_user_work_zone_path(user_session, end_slash=True) + data['name']
        create_directory(real_file_path)
        await update_display(websocket, user_session,["tree/"])

    elif data.get("type") == "file-explorer-to_parent_dir":
        cvd = user_session["current_viewing_directory"]
        assert cvd != "expl/"
        sp = get_path_spit_point(cvd, ignore_last_slash=True)
        user_session["current_viewing_directory"] = cvd[:sp + 1]
        await update_display(websocket, user_session, ["expl/"])

    elif data.get("type") == "file-explorer-to_sub_dir":
        user_session["current_viewing_directory"] = data["new_path"]
        await update_display(websocket, user_session,["expl/"])