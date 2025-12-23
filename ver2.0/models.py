import sqlite3
import json
import os
import hashlib
from typing import List, Dict, Optional, Tuple
from database import get_db_connection, init_db

# 确保模块加载时数据库已初始化
init_db()

class User:
    '''
    用户实体类
    封装用户基本信息及联系方式
    '''
    def __init__(self, id, username, role, status, contact_info):
        self.id = id
        self.username = username
        self.role = role
        self.status = status
        self.contact_info = contact_info

    @property
    def address(self):
        '''快捷属性：从 contact_info 字典中安全获取地址，若不存在返回空字符串'''
        return self.contact_info.get('address', '')

    @property
    def phone(self):
        '''快捷属性：从 contact_info 字典中安全获取电话'''
        return self.contact_info.get('phone', '')

    @property
    def email(self):
        '''快捷属性：从 contact_info 字典中安全获取邮箱'''
        return self.contact_info.get('email', '')

class Item:
    '''
    物品实体类
    包含物品的所有属性，以及为了方便UI显示而关联查询出的额外字段（如卖家名、类别名）
    '''
    def __init__(self, id, name, description, category_id, owner_id, status, price, can_bargain, address, specific_attributes, image_paths,
                 category_name=None, owner_username=None, phone=None, email=None, buyer_id=None, want_count=0):
        self.id = id
        self.name = name
        self.description = description
        self.category_id = category_id
        self.owner_id = owner_id
        self.status = status
        self.price = price
        self.can_bargain = can_bargain
        self.address = address
        self.specific_attributes = specific_attributes
        self.image_paths = image_paths
        self.buyer_id = buyer_id
        self.want_count = want_count
        
        # GUI 兼容性字段 (通过 JOIN 查询获取)
        self.category = category_name if category_name else str(category_id)
        self.owner_username = owner_username if owner_username else str(owner_id)
        self.phone = phone if phone else ""
        self.email = email if email else ""

    @property
    def item_id(self):
        return self.id

class Message:
    '''
    留言实体类
    '''
    def __init__(self, id, item_id, sender_id, sender_name, content, reply_to_id, created_at):
        self.id = id
        self.item_id = item_id
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.content = content
        self.reply_to_id = reply_to_id
        self.created_at = created_at

class Category:
    '''
    类别实体类
    包含类别名称和该类别特有的属性模板
    '''
    def __init__(self, id, name, attributes_template):
        self.id = id
        self.name = name
        self.attributes_template = attributes_template

class UserManager:
    '''
    用户管理器
    负责用户的认证、注册、审批及管理员管理
    '''
    def authenticate(self, username, password) -> Optional[User]:
        '''验证用户登录，检查密码哈希'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            salt = row['salt']
            stored_hash = row['password_hash']
            # 使用相同的盐和算法验证密码
            if hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000) == stored_hash:
                return User(row['id'], row['username'], row['role'], row['status'], json.loads(row['contact_info']))
        return None

    def get_user(self, username) -> Optional[User]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['role'], row['status'], json.loads(row['contact_info']))
        return None

    def register(self, username, password, contact_info: Dict) -> Tuple[bool, str]:
        '''注册新用户，密码加密存储，状态默认为 pending'''
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            salt = os.urandom(16)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role, status, contact_info) VALUES (?, ?, ?, ?, ?, ?)",
                (username, pwd_hash, salt, 'user', 'pending', json.dumps(contact_info, ensure_ascii=False))
            )
            conn.commit()
            return True, "注册成功，请等待管理员审核"
        except sqlite3.IntegrityError:
            return False, "用户名已存在"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

    def register_user(self, username, password, address, phone, email):
        '''GUI 兼容性包装器'''
        contact_info = {"address": address, "phone": phone, "email": email}
        success, msg = self.register(username, password, contact_info)
        if not success:
            raise ValueError(msg)
        return True

    def get_pending_users(self) -> List[User]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE status = 'pending'")
        rows = cursor.fetchall()
        conn.close()
        return [User(r['id'], r['username'], r['role'], r['status'], json.loads(r['contact_info'])) for r in rows]

    def get_all_users(self) -> List[User]:
        '''获取所有用户 (用于管理员界面)'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        return [User(r['id'], r['username'], r['role'], r['status'], json.loads(r['contact_info'])) for r in rows]

    def approve_user(self, username):
        '''管理员批准用户注册'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET status = 'approved' WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return True

    def has_admin(self) -> bool:
        '''检查数据库中是否存在管理员'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def create_admin(self, username, password):
        '''创建管理员账户'''
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            salt = os.urandom(16)
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
            contact = json.dumps({"address": "System", "phone": "", "email": ""}, ensure_ascii=False)
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt, role, status, contact_info) VALUES (?, ?, ?, ?, ?, ?)",
                (username, pwd_hash, salt, 'admin', 'approved', contact)
            )
            conn.commit()
            return True, "管理员创建成功"
        except Exception as e:
            return False, str(e)
        finally:
            conn.close()

class CategoryManager:
    '''
    类别管理器
    负责物品类别的增删改查，以及属性模板的管理
    '''
    def get_all(self) -> List[Category]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        rows = cursor.fetchall()
        conn.close()
        return [Category(r['id'], r['name'], json.loads(r['attributes_template'])) for r in rows]

    def get_all_categories(self) -> List[str]:
        '''GUI 兼容性: 返回类别名称列表'''
        return [c.name for c in self.get_all()]

    def add_category(self, name, attributes_template: Dict) -> bool:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name, attributes_template) VALUES (?, ?)", 
                           (name, json.dumps(attributes_template, ensure_ascii=False)))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def get_attributes_for_category(self, name: str) -> List[str]:
        '''获取指定类别的特定属性列表（用于动态生成表单）'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT attributes_template FROM categories WHERE name = ?", (name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row['attributes_template'])
        return []

    def update_category(self, name, attributes: List[str]):
        conn = get_db_connection()
        cursor = conn.cursor()
        # 注意：这里假设 name 不变，只更新属性。如果 name 变了需要 ID。
        # 简化起见，我们假设 GUI 传递的 name 是存在的。
        cursor.execute("UPDATE categories SET attributes_template = ? WHERE name = ?", 
                       (json.dumps(attributes, ensure_ascii=False), name))
        conn.commit()
        conn.close()

    def delete_category(self, name):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name = ?", (name,))
        conn.commit()
        conn.close()

class ItemManager:
    '''
    物品管理器
    负责物品的发布、搜索、交易流程及留言管理
    '''
    def _fetch_items(self, where_clause="", params=()) -> List[Item]:
        '''
        核心查询方法
        执行带有 JOIN 的 SQL 查询，将 items 表与 users, categories 表关联，
        并转换 JSON 字段为 Python 对象
        '''
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = '''
            SELECT i.*, c.name as category_name, u.username as owner_username, u.contact_info,
            (SELECT COUNT(*) FROM item_wants w WHERE w.item_id = i.id) as want_count
            FROM items i
            JOIN categories c ON i.category_id = c.id
            JOIN users u ON i.owner_id = u.id
        '''
        if where_clause:
            sql += f" WHERE {where_clause}"
            
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for r in rows:
            contact = json.loads(r['contact_info'])
            items.append(Item(
                id=r['id'],
                name=r['name'],
                description=r['description'],
                category_id=r['category_id'],
                owner_id=r['owner_id'],
                status=r['status'],
                price=r['price'],
                can_bargain=r['can_bargain'],
                address=r['address'],
                specific_attributes=json.loads(r['specific_attributes']),
                image_paths=json.loads(r['image_paths']),
                category_name=r['category_name'],
                owner_username=r['owner_username'],
                phone=contact.get('phone', ''),
                email=contact.get('email', ''),
                buyer_id=r['buyer_id'],
                want_count=r['want_count']
            ))
        return items

    def create_item(self, name, description, price, can_bargain, address, phone, email, category, owner_username, specific_attributes, image_paths=None):
        '''创建新物品，处理外键关联和 JSON 数据序列化'''
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 1. 获取 category_id
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category,))
            cat_row = cursor.fetchone()
            if not cat_row:
                raise ValueError(f"Category '{category}' not found")
            category_id = cat_row['id']
            
            # 2. 获取 owner_id
            cursor.execute("SELECT id FROM users WHERE username = ?", (owner_username,))
            user_row = cursor.fetchone()
            if not user_row:
                raise ValueError(f"User '{owner_username}' not found")
            owner_id = user_row['id']
            
            # 3. 插入物品
            if image_paths is None:
                image_paths = []
            
            cursor.execute('''
                INSERT INTO items (name, description, category_id, owner_id, price, can_bargain, address, specific_attributes, image_paths)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, description, category_id, owner_id, price, can_bargain, address, json.dumps(specific_attributes, ensure_ascii=False), json.dumps(image_paths, ensure_ascii=False)))
            conn.commit()
        finally:
            conn.close()

    def get_all_items(self) -> List[Item]:
        '''获取所有物品 (包括已售出)'''
        return self._fetch_items()

    def search_items(self, category_name, keyword) -> List[Item]:
        '''根据类别和关键字搜索物品'''
        # 先获取 category_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return []
            
        category_id = row['id']
        
        where = "i.category_id = ?"
        params = []
        params.append(category_id)
        
        if keyword:
            where += " AND (i.name LIKE ? OR i.description LIKE ? OR u.username LIKE ?)"
            kw = f"%{keyword}%"
            params.extend([kw, kw, kw])
            
        return self._fetch_items(where, tuple(params))

    def find_item_by_id(self, item_id) -> Optional[Item]:
        items = self._fetch_items("i.id = ?", (item_id,))
        return items[0] if items else None

    def delete_item(self, item_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def revise_item(self, item_id, data: Dict):
        '''更新物品信息'''
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建更新语句
        fields = []
        values = []
        if 'name' in data:
            fields.append("name = ?")
            values.append(data['name'])
        if 'description' in data:
            fields.append("description = ?")
            values.append(data['description'])
        if 'price' in data:
            fields.append("price = ?")
            values.append(data['price'])
        if 'can_bargain' in data:
            fields.append("can_bargain = ?")
            values.append(data['can_bargain'])
        if 'address' in data:
            fields.append("address = ?")
            values.append(data['address'])
        if 'image_paths' in data:
            fields.append("image_paths = ?")
            values.append(json.dumps(data['image_paths'], ensure_ascii=False))
        if 'specific_attributes' in data:
            fields.append("specific_attributes = ?")
            values.append(json.dumps(data['specific_attributes'], ensure_ascii=False))
            
        if fields:
            values.append(item_id)
            sql = f"UPDATE items SET {', '.join(fields)} WHERE id = ?"
            cursor.execute(sql, values)
            conn.commit()
        conn.close()

    def add_want(self, item_id, user_id, offer_price=0.0) -> bool:
        '''记录用户对物品的购买意向'''
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO item_wants (item_id, user_id, offer_price) VALUES (?, ?, ?)", (item_id, user_id, offer_price))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False # 已经想要了
        finally:
            conn.close()

    def get_item_wanters(self, item_id) -> List[User]:
        '''获取想要该物品的所有用户'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.* FROM users u 
            JOIN item_wants w ON w.user_id = u.id 
            WHERE w.item_id = ?
        ''', (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return [User(r['id'], r['username'], r['role'], r['status'], json.loads(r['contact_info'])) for r in rows]

    def get_user_wants(self, user_id) -> List[Item]:
        '''获取用户想要的所有物品'''
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = '''
            SELECT i.*, c.name as category_name, u.username as owner_username, u.contact_info,
            (SELECT COUNT(*) FROM item_wants w2 WHERE w2.item_id = i.id) as want_count
            FROM items i
            JOIN item_wants w ON i.id = w.item_id
            JOIN categories c ON i.category_id = c.id
            JOIN users u ON i.owner_id = u.id
            WHERE w.user_id = ?
        '''
        cursor.execute(sql, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        items = []
        for r in rows:
            contact = json.loads(r['contact_info'])
            items.append(Item(
                id=r['id'],
                name=r['name'],
                description=r['description'],
                category_id=r['category_id'],
                owner_id=r['owner_id'],
                status=r['status'],
                price=r['price'],
                can_bargain=r['can_bargain'],
                address=r['address'],
                specific_attributes=json.loads(r['specific_attributes']),
                image_paths=json.loads(r['image_paths']),
                category_name=r['category_name'],
                owner_username=r['owner_username'],
                phone=contact.get('phone', ''),
                email=contact.get('email', ''),
                buyer_id=r['buyer_id'],
                want_count=r['want_count']
            ))
        return items

    def get_received_wants(self, owner_id) -> List[Dict]:
        '''获取卖家收到的所有意向信息'''
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = '''
            SELECT i.name as item_name, u.username as buyer_name, u.contact_info, w.offer_price
            FROM item_wants w
            JOIN items i ON w.item_id = i.id
            JOIN users u ON w.user_id = u.id
            WHERE i.owner_id = ?
        '''
        cursor.execute(sql, (owner_id,))
        rows = cursor.fetchall()
        conn.close()
        results = []
        for r in rows:
            contact = json.loads(r['contact_info'])
            results.append({
                'item_name': r['item_name'],
                'buyer_name': r['buyer_name'],
                'phone': contact.get('phone', ''),
                'address': contact.get('address', ''),
                'offer_price': r['offer_price']
            })
        return results

    def confirm_sold(self, item_id, buyer_id):
        '''确认交易完成：将状态改为已售出，并记录最终买家'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE items SET status = 'sold', buyer_id = ? WHERE id = ?", (buyer_id, item_id))
        conn.commit()
        conn.close()

    def add_message(self, item_id, sender_id, content, reply_to_id=None):
        '''添加留言'''
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO messages (item_id, sender_id, content, reply_to_id) VALUES (?, ?, ?, ?)",
            (item_id, sender_id, content, reply_to_id)
        )
        conn.commit()
        conn.close()

    def get_messages(self, item_id) -> List[Message]:
        '''获取物品的所有留言'''
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = '''
            SELECT m.*, u.username as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.item_id = ?
            ORDER BY m.created_at ASC
        '''
        cursor.execute(sql, (item_id,))
        rows = cursor.fetchall()
        conn.close()
        return [Message(r['id'], r['item_id'], r['sender_id'], r['sender_name'], r['content'], r['reply_to_id'], r['created_at']) for r in rows]