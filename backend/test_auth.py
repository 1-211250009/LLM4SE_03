"""测试认证功能的脚本"""

import sys
import asyncio
from app.core.database import SessionLocal
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin
from app.services.auth_service import AuthService
from app.core.security import verify_password

def test_register():
    """测试注册功能"""
    print("\n" + "="*50)
    print("测试注册功能")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 测试数据
        test_user = UserRegister(
            email="test_new_user@example.com",
            password="test123456",
            name="测试用户"
        )
        
        print(f"\n📝 注册数据:")
        print(f"  邮箱: {test_user.email}")
        print(f"  密码: {test_user.password}")
        print(f"  姓名: {test_user.name}")
        
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == test_user.email).first()
        if existing_user:
            print(f"\n⚠️  用户已存在，删除后重试...")
            db.delete(existing_user)
            db.commit()
        
        # 尝试注册
        print(f"\n🔄 开始注册...")
        user = AuthService.register_user(db, test_user)
        
        print(f"\n✅ 注册成功!")
        print(f"  用户ID: {user.id}")
        print(f"  邮箱: {user.email}")
        print(f"  姓名: {user.name}")
        print(f"  密码哈希: {user.password_hash[:50]}...")
        
        # 验证密码
        password_valid = verify_password(test_user.password, user.password_hash)
        print(f"\n🔐 密码验证: {'✅ 通过' if password_valid else '❌ 失败'}")
        
        return user
        
    except Exception as e:
        print(f"\n❌ 注册失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

def test_login(email, password):
    """测试登录功能"""
    print("\n" + "="*50)
    print("测试登录功能")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        # 测试数据
        login_data = UserLogin(
            email=email,
            password=password
        )
        
        print(f"\n📝 登录数据:")
        print(f"  邮箱: {login_data.email}")
        print(f"  密码: {login_data.password}")
        
        # 尝试登录
        print(f"\n🔄 开始登录...")
        user = AuthService.authenticate_user(db, login_data)
        
        print(f"\n✅ 登录成功!")
        print(f"  用户ID: {user.id}")
        print(f"  邮箱: {user.email}")
        print(f"  姓名: {user.name}")
        
        # 创建Token
        tokens = AuthService.create_tokens(user.id)
        print(f"\n🔑 Token创建成功:")
        print(f"  Access Token: {tokens['access_token'][:50]}...")
        print(f"  Refresh Token: {tokens['refresh_token'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 登录失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def check_existing_users():
    """检查现有用户"""
    print("\n" + "="*50)
    print("检查数据库中的现有用户")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        users = db.query(User).all()
        print(f"\n📊 共有 {len(users)} 个用户:")
        
        for i, user in enumerate(users, 1):
            print(f"\n用户 #{i}:")
            print(f"  ID: {user.id}")
            print(f"  邮箱: {user.email}")
            print(f"  姓名: {user.name}")
            print(f"  创建时间: {user.created_at}")
        
        return users
        
    finally:
        db.close()

if __name__ == "__main__":
    print("\n" + "🧪 " + "="*48)
    print("🧪  AI旅行规划师 - 认证功能测试")
    print("🧪 " + "="*48)
    
    # 1. 检查现有用户
    existing_users = check_existing_users()
    
    # 2. 测试注册
    registered_user = test_register()
    
    # 3. 测试登录
    if registered_user:
        test_login("test_new_user@example.com", "test123456")
    
    # 4. 测试使用已存在的用户登录
    if existing_users:
        print("\n" + "="*50)
        print("提示：您可以尝试使用以下账号登录")
        print("="*50)
        for user in existing_users[:3]:  # 显示前3个
            print(f"\n  邮箱: {user.email}")
            print(f"  密码: (未知，可能是 '123456' 或 'password')")
    
    print("\n" + "="*50)
    print("测试完成!")
    print("="*50 + "\n")

