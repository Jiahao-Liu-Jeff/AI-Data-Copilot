"""用户对话持久化模块 - SQLite 存储不同用户的对话历史"""
import json
import os
import sqlite3
from datetime import datetime
from typing import List, Optional, Dict, Any


class UserMemoryStore:
    """用户对话记忆存储器"""

    def __init__(self, db_path: str = "data/memory.db"):
        """
        初始化存储器

        Args:
            db_path: SQLite 数据库路径
        """
        self.db_path = db_path
        # 确保目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_table()

    def _init_table(self) -> None:
        """初始化表结构"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                conversation_id TEXT NOT NULL,
                conversation_title TEXT,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, conversation_id)
            )
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_conv
            ON user_memories(user_id, conversation_id)
        """)
        self.conn.commit()

    def save(
        self,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        conversation_title: str = None
    ) -> None:
        """
        保存用户对话记忆

        Args:
            user_id: 用户标识
            conversation_id: 会话标识
            messages: 消息列表（LangChain 格式）
            conversation_title: 会话标题（第一个问题）
        """
        messages_json = json.dumps(messages, ensure_ascii=False)
        now = datetime.now().isoformat()

        self.conn.execute("""
            INSERT INTO user_memories (user_id, conversation_id, conversation_title, messages, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, conversation_id)
            DO UPDATE SET messages = excluded.messages, conversation_title = COALESCE(excluded.conversation_title, user_memories.conversation_title), updated_at = excluded.updated_at
        """, (user_id, conversation_id, conversation_title, messages_json, now))
        self.conn.commit()

    def load(
        self,
        user_id: str,
        conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        加载用户对话记忆

        Args:
            user_id: 用户标识
            conversation_id: 会话标识

        Returns:
            消息列表，如果不存在返回空列表
        """
        cursor = self.conn.execute("""
            SELECT messages FROM user_memories
            WHERE user_id = ? AND conversation_id = ?
        """, (user_id, conversation_id))

        row = cursor.fetchone()
        if row is None:
            return []

        return json.loads(row[0])

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """
        列出用户的所有会话

        Args:
            user_id: 用户标识

        Returns:
            会话列表，包含 conversation_id, conversation_title, updated_at
        """
        cursor = self.conn.execute("""
            SELECT conversation_id, conversation_title, updated_at FROM user_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,))

        return [
            {
                "conversation_id": row[0],
                "conversation_title": row[1] if row[1] else row[0],
                "updated_at": row[2]
            }
            for row in cursor.fetchall()
        ]

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        """
        删除用户的某个会话

        Args:
            user_id: 用户标识
            conversation_id: 会话标识

        Returns:
            是否删除成功
        """
        cursor = self.conn.execute("""
            DELETE FROM user_memories
            WHERE user_id = ? AND conversation_id = ?
        """, (user_id, conversation_id))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_all_for_user(self, user_id: str) -> int:
        """
        删除用户的所有会话

        Args:
            user_id: 用户标识

        Returns:
            删除的会话数量
        """
        cursor = self.conn.execute("""
            DELETE FROM user_memories
            WHERE user_id = ?
        """, (user_id,))
        self.conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """关闭数据库连接"""
        self.conn.close()


# 全局单例实例
_memory_store: Optional[UserMemoryStore] = None


def get_memory_store() -> UserMemoryStore:
    """获取全局记忆存储器实例"""
    global _memory_store
    if _memory_store is None:
        _memory_store = UserMemoryStore()
    return _memory_store
