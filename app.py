from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
# 生产环境使用更安全的密钥
app.secret_key = os.environ.get('SECRET_KEY', 'item_manager_secret_key_2024')

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'item_manager.db')

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建物品表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            quantity INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建记录表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            record_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # 创建管理员账号
    cursor.execute("SELECT * FROM users WHERE username = 'user'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, name, role) VALUES (?, ?, ?)",
            ('user', '管理员', 'admin')
        )
    
    # 创建默认物品（如果不存在）
    cursor.execute("SELECT COUNT(*) FROM items")
    if cursor.fetchone()[0] == 0:
        default_items = [
            ('笔记本电脑', 5),
            ('投影仪', 2),
            ('移动硬盘', 10),
            ('相机', 3),
            ('三脚架', 4),
            ('充电宝', 8),
            ('数据线', 20),
            ('U盘', 15)
        ]
        cursor.executemany(
            "INSERT INTO items (name, quantity, sort_order) VALUES (?, ?, ?)",
            [(item[0], item[1], idx) for idx, item in enumerate(default_items)]
        )
    
    conn.commit()
    conn.close()

# 初始化数据库
init_db()

# ==================== 路由 ====================

@app.route('/')
def index():
    """登录页面"""
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user_home'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    """登录处理"""
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'})
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['name'] = user['name']
        session['role'] = user['role']
        
        # 普通用户首次登录需要修改姓名
        if user['role'] == 'user' and user['name'] == user['username']:
            return jsonify({'success': True, 'need_change_name': True, 'role': 'user'})
        
        return jsonify({'success': True, 'role': user['role']})
    else:
        # 自动创建普通用户
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, name, role) VALUES (?, ?, ?)",
            (username, username, 'user')
        )
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        session['name'] = username
        session['role'] = 'user'
        
        return jsonify({'success': True, 'need_change_name': True, 'role': 'user'})

@app.route('/update_name', methods=['POST'])
def update_name():
    """更新用户姓名"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': '姓名不能为空'})
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, session['user_id']))
    conn.commit()
    conn.close()
    
    session['name'] = name
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('index'))

# ==================== 普通用户页面 ====================

@app.route('/user')
def user_home():
    """普通用户首页"""
    if session.get('role') != 'user':
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有物品
    cursor.execute("SELECT * FROM items ORDER BY name")
    items = cursor.fetchall()
    
    # 获取当前用户的借用记录
    cursor.execute("""
        SELECT r.*, i.name as item_name, u.name as user_name
        FROM records r
        JOIN items i ON r.item_id = i.id
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id = ? AND r.type = 'borrow'
        ORDER BY r.record_time DESC
    """, (session['user_id'],))
    borrow_records = cursor.fetchall()
    
    # 计算每个物品已借数量
    borrowed = {}
    for record in borrow_records:
        if record['item_id'] not in borrowed:
            borrowed[record['item_id']] = 0
        borrowed[record['item_id']] += record['quantity']
    
    conn.close()
    return render_template('user.html', items=items, borrow_records=borrow_records, borrowed=borrowed)

@app.route('/borrow', methods=['POST'])
def borrow():
    """借用物品"""
    if session.get('role') != 'user':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    notes = data.get('notes', '')
    
    if not item_id or not quantity or int(quantity) <= 0:
        return jsonify({'success': False, 'message': '请选择物品并填写正确的数量'})
    
    quantity = int(quantity)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查物品库存
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({'success': False, 'message': '物品不存在'})
    
    # 计算已借数量
    cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0) as borrowed
        FROM records
        WHERE item_id = ? AND user_id = ? AND type = 'borrow'
    """, (item_id, session['user_id']))
    borrowed = cursor.fetchone()['borrowed']
    
    # 计算已还数量
    cursor.execute("""
        SELECT COALESCE(SUM(quantity), 0) as returned
        FROM records
        WHERE item_id = ? AND user_id = ? AND type = 'return'
    """, (item_id, session['user_id']))
    returned = cursor.fetchone()['returned']
    
    available = item['quantity'] - (borrowed - returned)
    
    if quantity > available:
        conn.close()
        return jsonify({'success': False, 'message': f'库存不足，当前可借数量: {available}'})
    
    # 添加借用记录
    cursor.execute(
        "INSERT INTO records (item_id, user_id, type, quantity, notes) VALUES (?, ?, ?, ?, ?)",
        (item_id, session['user_id'], 'borrow', quantity, notes)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '借用成功'})

@app.route('/return_item', methods=['POST'])
def return_item():
    """归还物品"""
    if session.get('role') != 'user':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    notes = data.get('notes', '')
    
    if not item_id or not quantity or int(quantity) <= 0:
        return jsonify({'success': False, 'message': '请选择物品并填写正确的数量'})
    
    quantity = int(quantity)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 计算已借未还数量
    cursor.execute("""
        SELECT COALESCE(SUM(CASE WHEN type = 'borrow' THEN quantity ELSE -quantity END), 0) as remaining
        FROM records
        WHERE item_id = ? AND user_id = ?
    """, (item_id, session['user_id']))
    remaining = cursor.fetchone()['remaining']
    
    if quantity > remaining:
        conn.close()
        return jsonify({'success': False, 'message': f'您只借用了 {remaining} 件，已全部归还'})
    
    # 添加归还记录
    cursor.execute(
        "INSERT INTO records (item_id, user_id, type, quantity, notes) VALUES (?, ?, ?, ?, ?)",
        (item_id, session['user_id'], 'return', quantity, notes)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '归还成功'})

# ==================== 管理员页面 ====================

@app.route('/admin')
def admin():
    """管理员首页"""
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有物品（按sort_order排序）
    cursor.execute("SELECT * FROM items ORDER BY sort_order ASC, name ASC")
    items = cursor.fetchall()
    
    # 获取所有记录
    cursor.execute("""
        SELECT r.*, i.name as item_name, u.name as user_name, u.username
        FROM records r
        JOIN items i ON r.item_id = i.id
        JOIN users u ON r.user_id = u.id
        ORDER BY r.record_time DESC
    """)
    records = cursor.fetchall()
    
    # 统计
    cursor.execute("SELECT COUNT(*) as total FROM items")
    item_count = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'user'")
    user_count = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM records")
    record_count = cursor.fetchone()['total']
    
    conn.close()
    
    return render_template('admin.html', items=items, records=records, 
                          item_count=item_count, user_count=user_count, record_count=record_count)

@app.route('/admin/add_item', methods=['POST'])
def admin_add_item():
    """管理员添加物品"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    name = data.get('name', '').strip()
    quantity = data.get('quantity', 0)
    
    if not name:
        return jsonify({'success': False, 'message': '物品名称不能为空'})
    
    quantity = int(quantity) if quantity else 0
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查物品是否存在
    cursor.execute("SELECT * FROM items WHERE name = ?", (name,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '物品已存在'})
    
    # 获取最大的sort_order
    cursor.execute("SELECT COALESCE(MAX(sort_order), -1) as max_order FROM items")
    max_order = cursor.fetchone()['max_order']
    
    cursor.execute("INSERT INTO items (name, quantity, sort_order) VALUES (?, ?, ?)", (name, quantity, max_order + 1))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '添加成功'})

@app.route('/admin/update_item', methods=['POST'])
def admin_update_item():
    """管理员修改物品"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    item_id = data.get('id')
    name = data.get('name', '').strip()
    quantity = data.get('quantity')
    
    if not name or quantity is None:
        return jsonify({'success': False, 'message': '请填写完整的物品信息'})
    
    quantity = int(quantity)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查名称是否与其他物品重复
    cursor.execute("SELECT * FROM items WHERE name = ? AND id != ?", (name, item_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': '物品名称已存在'})
    
    cursor.execute("UPDATE items SET name = ?, quantity = ? WHERE id = ?", 
                   (name, quantity, item_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '修改成功'})

@app.route('/admin/delete_item', methods=['POST'])
def admin_delete_item():
    """管理员删除物品"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    item_id = data.get('id')
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查是否有借用记录
    cursor.execute("SELECT COUNT(*) FROM records WHERE item_id = ?", (item_id,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        return jsonify({'success': False, 'message': '该物品有借用记录，无法删除'})
    
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '删除成功'})

@app.route('/admin/update_record', methods=['POST'])
def admin_update_record():
    """管理员修改记录"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    record_id = data.get('id')
    quantity = data.get('quantity')
    
    if quantity is None or int(quantity) <= 0:
        return jsonify({'success': False, 'message': '数量必须大于0'})
    
    quantity = int(quantity)
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("UPDATE records SET quantity = ? WHERE id = ?", (quantity, record_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '修改成功'})

@app.route('/admin/delete_record', methods=['POST'])
def admin_delete_record():
    """管理员删除记录"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    record_id = data.get('id')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '删除成功'})

@app.route('/admin/sort_items', methods=['POST'])
def admin_sort_items():
    """管理员排序物品"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    order = data.get('order', 'asc')
    
    conn = get_db()
    cursor = conn.cursor()
    
    if order == 'desc':
        cursor.execute("SELECT * FROM items ORDER BY sort_order DESC, name DESC")
    else:
        cursor.execute("SELECT * FROM items ORDER BY sort_order ASC, name ASC")
    
    items = cursor.fetchall()
    conn.close()
    
    items_list = []
    for item in items:
        items_list.append({
            'id': item['id'],
            'name': item['name'],
            'quantity': item['quantity']
        })
    
    return jsonify({'success': True, 'items': items_list})

@app.route('/admin/save_order', methods=['POST'])
def admin_save_order():
    """保存物品排序顺序"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    order_list = data.get('order', [])
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 更新每个物品的sort_order
    for idx, item_id in enumerate(order_list):
        cursor.execute("UPDATE items SET sort_order = ? WHERE id = ?", (idx, item_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '顺序已保存'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
