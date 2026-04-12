"""密码加密工具函数。

使用 passlib + bcrypt 进行密码哈希，不存储明文密码。
bcrypt 是单向哈希，无法从哈希值反推出原始密码。
"""

from passlib.hash import bcrypt


def hash_password(plain_password: str) -> str:
    """将明文密码转为 bcrypt 哈希值。

    Args:
        plain_password: 用户输入的明文密码
    Returns:
        哈希后的字符串，用于存入数据库
    """
    return bcrypt.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """验证明文密码是否与哈希值匹配。

    Args:
        plain_password: 用户输入的明文密码
        password_hash: 数据库中存储的哈希值
    Returns:
        匹配返回 True，否则返回 False
    """
    return bcrypt.verify(plain_password, password_hash)
