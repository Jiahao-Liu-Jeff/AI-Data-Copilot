"""用户认证模块"""
import json
import os
from typing import Optional, Dict

USERS_FILE = "data/users.json"


def load_users() -> Dict:
    """加载用户数据"""
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_user(username: str, password: str) -> Optional[Dict]:
    """
    验证用户登录

    Args:
        username: 用户名
        password: 密码

    Returns:
        用户信息 dict，如果验证失败返回 None
    """
    users = load_users()
    if username in users:
        user = users[username]
        if user["password"] == password:
            return {
                "username": username,
                "role": user.get("role", "normal"),
                "display_name": user.get("display_name", username)
            }
    return None


def get_user_info(username: str) -> Optional[Dict]:
    """获取用户信息"""
    users = load_users()
    if username in users:
        user = users[username]
        return {
            "username": username,
            "role": user.get("role", "normal"),
            "display_name": user.get("display_name", username)
        }
    return None


def is_admin(username: str) -> bool:
    """检查用户是否为管理员"""
    user = get_user_info(username)
    return user is not None and user.get("role") == "admin"


def add_user(username: str, password: str, role: str = "normal", display_name: str = None) -> bool:
    """
    添加用户

    Args:
        username: 用户名
        password: 密码
        role: 用户角色 ('normal' 或 'admin')
        display_name: 显示名称

    Returns:
        是否添加成功
    """
    users = load_users()
    if username in users:
        return False

    users[username] = {
        "password": password,
        "role": role,
        "display_name": display_name or username
    }

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

    return True
