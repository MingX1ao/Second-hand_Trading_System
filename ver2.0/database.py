import sqlite3
import os
import json

DB_FILE = 'second_hand.db'

def get_db_connection():
    '''
    获取数据库连接
    配置 row_factory 以便可以通过列名访问数据
    '''
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # 允许通过列名访问数据
    return conn

def init_db():
    '''
    初始化数据库表结构
    如果数据库不存在，将创建所有必要的表和默认数据
    '''
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 开启外键支持
    cursor.execute("PRAGMA foreign_keys = ON")

    # 初始化图片存储目录
    if not os.path.exists('ITEM_IMG'):
        os.makedirs('ITEM_IMG')

    # 1. 用户表 - 存储账户信息、密码哈希、角色状态和联系方式
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash BLOB NOT NULL,
            salt BLOB NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
            status TEXT NOT NULL CHECK(status IN ('pending', 'approved')),
            contact_info TEXT NOT NULL -- JSON string
        )
    ''')

    # 2. 物品类别表 - 存储类别名称及该类别特有的属性模板(JSON)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            attributes_template TEXT NOT NULL -- JSON string
        )
    ''')
    
    # 初始化默认类别 (仅当表中无数据时执行)
    cursor.execute("SELECT count(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("书籍", ["作者", "出版社", "ISBN", "出版年份"]),
            ("电子产品", ["品牌", "型号", "购买日期", "保修期"]),
            ("食品", ["保质期", "生产日期", "净含量", "成分"]),
            ("服装", ["尺码", "材质", "适用性别", "颜色"])
        ]
        for name, attrs in default_categories:
            cursor.execute("INSERT INTO categories (name, attributes_template) VALUES (?, ?)", (name, json.dumps(attrs, ensure_ascii=False)))
        print(f"系统初始化: 已添加 {len(default_categories)} 个默认类别")

    # 3. 物品表 - 核心表，存储物品详情、状态、价格及所有者外键
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category_id INTEGER NOT NULL,
            owner_id INTEGER NOT NULL,
            buyer_id INTEGER, -- 记录买家ID
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'reserved', 'sold')),
            price REAL DEFAULT 0.0,
            can_bargain INTEGER DEFAULT 0, -- 0 for No, 1 for Yes
            address TEXT, -- Item location
            specific_attributes TEXT DEFAULT '{}', -- JSON string
            image_paths TEXT DEFAULT '[]', -- JSON string list
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id),
            FOREIGN KEY (owner_id) REFERENCES users (id),
            FOREIGN KEY (buyer_id) REFERENCES users (id)
        )
    ''')
    
    # 4. 物品意向表 - 多对多关联表，记录买家对物品的购买意向和出价
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_wants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            offer_price REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (item_id) REFERENCES items (id),
            UNIQUE(user_id, item_id)
        )
    ''')

    # 5. 留言表 - 存储物品详情页下的用户留言和回复
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            reply_to_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (reply_to_id) REFERENCES messages (id)
        )
    ''')

    conn.commit()
    conn.close()