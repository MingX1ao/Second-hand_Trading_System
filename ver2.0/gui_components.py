import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from typing import Dict, List, Optional
import os
import shutil
import uuid
from PIL import Image, ImageTk
from models import User, Item, CategoryManager, UserManager, ItemManager

# --- 基础/辅助窗口 ---

class RegisterWindow(tk.Toplevel):
    '''
    注册窗口
    '''
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.title("用户注册")
        self.user_manager = user_manager
        self.geometry("350x250")

        self.entries: Dict[str, tk.Entry] = {}
        fields = ["用户名", "密码", "确认密码", "地址", "手机", "邮箱"]
        
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill="both", expand=True)

        for i, field in enumerate(fields):
            ttk.Label(frame, text=f"{field}:").grid(row=i, column=0, sticky="w", pady=2)
            entry_type = tk.Entry
            
            # 密码相关字段需要保护
            if "密码" in field:
                entry_type = lambda master: tk.Entry(master, show="*")
            
            # 缓存信息输入
            entry = entry_type(frame)
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            self.entries[field] = entry
        
        frame.columnconfigure(1, weight=1)

        ttk.Button(frame, text="注册", command=self.do_register).grid(row=len(fields), column=0, columnspan=2, pady=10)

    def do_register(self):
        '''
        执行注册行为
        '''
        vals = {key: entry.get().strip() for key, entry in self.entries.items()}    # 获取缓存中的输入
        
        if not all(vals.values()):
            messagebox.showerror("错误", "所有字段都不能为空！", parent=self)
            return
        if vals["密码"] != vals["确认密码"]:
            messagebox.showerror("错误", "两次输入的密码不一致！", parent=self)
            return

        try:
            # 转化为df进行数据库写入
            self.user_manager.register_user(
                username=vals["用户名"],
                password=vals["密码"],
                address=vals["地址"],
                phone=vals["手机"],
                email=vals["邮箱"]
            )
            messagebox.showinfo("成功", "注册成功！请等待管理员审批。", parent=self)
            self.destroy()
        except ValueError as e:
            messagebox.showerror("错误", str(e), parent=self)


# --- 初始化管理员视图 ---

class CreateAdminView(ttk.Frame):
    '''
    初始化管理员账户视图 (当系统没有管理员时显示)
    '''
    def __init__(self, parent, app_controller):
        super().__init__(parent, padding="20")
        self.app_controller = app_controller
        
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        frame = ttk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(frame, text="系统初始化 - 创建管理员", font=("", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(frame, text="管理员用户名:").grid(row=1, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.insert(0, "admin") # 默认用户名
        self.username_entry.grid(row=1, column=1, sticky="ew")

        ttk.Label(frame, text="密码:").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=2, column=1, sticky="ew")

        ttk.Label(frame, text="确认密码:").grid(row=3, column=0, sticky="w", pady=5)
        self.confirm_entry = ttk.Entry(frame, show="*")
        self.confirm_entry.grid(row=3, column=1, sticky="ew")

        ttk.Button(frame, text="创建管理员", command=self.create_admin).grid(row=4, column=0, columnspan=2, pady=20)

    def create_admin(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if not username or not password:
            messagebox.showerror("错误", "用户名和密码不能为空", parent=self)
            return
        
        if password != confirm:
            messagebox.showerror("错误", "两次输入的密码不一致", parent=self)
            return

        success, msg = self.app_controller.user_manager.create_admin(username, password)
        if success:
            messagebox.showinfo("成功", "管理员账户创建成功，请登录。", parent=self)
            self.app_controller.show_login_view()
        else:
            messagebox.showerror("错误", f"创建失败: {msg}", parent=self)

# --- 登录视图 ---

class LoginView(ttk.Frame):
    '''
    新的登录视图，作为一个Frame嵌入主窗口
    '''
    def __init__(self, parent: ttk.Frame, app_controller):
        super().__init__(parent, padding="20")
        self.app_controller = app_controller

        # 调整布局
        self.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        frame = ttk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Label(frame, text="用户名:").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(frame)
        self.username_entry.grid(row=0, column=1, sticky="ew")

        ttk.Label(frame, text="密码:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew")

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="登录", command=self.attempt_login).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="注册", command=self.open_register).pack(side="left", padx=5)

    def attempt_login(self):
        '''
        获取输入并尝试登录
        '''
        username = self.username_entry.get()
        password = self.password_entry.get()
        self.app_controller.attempt_login(username, password)   # 调用App的函数

    def open_register(self):
        '''
        打开注册界面
        '''
        RegisterWindow(self, self.app_controller.user_manager)

# --- 管理员专用窗口 ---

class CategoryManagementWindow(tk.Toplevel):
    '''
    类别管理窗口
    '''
    def __init__(self, parent, category_manager: CategoryManager):
        super().__init__(parent)
        self.title("类别管理")
        self.category_manager = category_manager
        self.geometry("400x350")
        
        # 左侧是已有类别目录
        left_frame = ttk.Frame(self, padding=5)
        left_frame.pack(side="left", fill="y")
        
        ttk.Label(left_frame, text="所有类别").pack()
        self.category_listbox = tk.Listbox(left_frame)
        self.category_listbox.pack(fill="y", expand=True)
        self.category_listbox.bind("<<ListboxSelect>>", self.on_category_select)
        
        # 右侧是当前选中的类别的详细内容
        right_frame = ttk.Frame(self, padding=5)
        right_frame.pack(side="right", fill="both", expand=True)

        ttk.Label(right_frame, text="类别名称:").pack(anchor="w")
        self.name_entry = ttk.Entry(right_frame)
        self.name_entry.pack(fill="x", pady=5)

        ttk.Label(right_frame, text="属性 (每行一个):").pack(anchor="w")
        self.attr_text = tk.Text(right_frame, height=8)
        self.attr_text.pack(fill="both", expand=True, pady=5)
        
        # 针对类别的操作
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="新建", command=self.clear_fields).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="保存", command=self.save_category).pack(side="left", expand=True)
        ttk.Button(btn_frame, text="删除", command=self.delete_category).pack(side="left", expand=True)

        self.refresh_list()     # 更新类别列表

    def refresh_list(self):
        self.category_listbox.delete(0, tk.END)     # 先清空列表
        # 获取所有类别并显示
        for cat_name in self.category_manager.get_all_categories():
            self.category_listbox.insert(tk.END, cat_name)
    
    def on_category_select(self, event=None):
        '''
        在右侧显示当前选中的类别的详细信息
        '''
        selection_indices = self.category_listbox.curselection()
        if not selection_indices:
            return
        
        cat_name = self.category_listbox.get(selection_indices[0])
        attributes = self.category_manager.get_attributes_for_category(cat_name)

        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, cat_name)
        
        self.attr_text.delete("1.0", tk.END)
        self.attr_text.insert("1.0", "\n".join(attributes))

    def clear_fields(self):
        '''
        清空显示的类别详细信息，对类别本身无影响
        '''
        self.name_entry.delete(0, tk.END)
        self.attr_text.delete("1.0", tk.END)
        self.category_listbox.selection_clear(0, tk.END)

    def save_category(self):
        '''
        保存当前显示的类别信息
        '''
        cat_name = self.name_entry.get().strip()
        if not cat_name:
            messagebox.showerror("错误", "类别名称不能为空！", parent=self)
            return
        
        # 按照换行进行类别项目构建
        attributes = [line.strip() for line in self.attr_text.get("1.0", tk.END).strip().split("\n") if line.strip()]
        
        # 检查是更新现有类别还是新建类别
        if cat_name in self.category_manager.get_all_categories():
            self.category_manager.update_category(cat_name, attributes)
            messagebox.showinfo("成功", f"类别 '{cat_name}' 已更新。", parent=self)
        else:
            if self.category_manager.add_category(cat_name, attributes):
                messagebox.showinfo("成功", f"类别 '{cat_name}' 已创建。", parent=self)
            else:
                messagebox.showerror("错误", "创建类别失败（可能是名称重复）。", parent=self)
                
        self.refresh_list()     # 更新显示列表

    def delete_category(self):
        '''
        删除选中的类别
        '''
        selection_indices = self.category_listbox.curselection()
        if not selection_indices:
            messagebox.showwarning("提示", "请先选择一个要删除的类别。", parent=self)
            return

        cat_name = self.category_listbox.get(selection_indices[0])
        if messagebox.askyesno("确认删除", f"确定要删除类别 '{cat_name}' 吗？", parent=self):
            self.category_manager.delete_category(cat_name)     # 删除类别
            self.refresh_list()
            self.clear_fields()


class UserManagementWindow(tk.Toplevel):
    '''
    用户管理窗口
    '''
    def __init__(self, parent, user_manager: UserManager):
        super().__init__(parent)
        self.title("用户管理")
        self.user_manager = user_manager
        self.geometry("600x400")
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ('username', 'role', 'status', 'address', 'phone')
        self.tree = ttk.Treeview(frame, columns=columns, show='headings')
        self.tree.heading('username', text='用户名')
        self.tree.heading('role', text='角色')
        self.tree.heading('status', text='状态')
        self.tree.heading('address', text='地址')
        self.tree.heading('phone', text='手机')
        self.tree.pack(fill="both", expand=True)
        
        self.refresh_users()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="批准选中用户", command=self.approve_selected).pack()

    def refresh_users(self):
        '''
        更新用户列表
        '''
        # 先删除
        for i in self.tree.get_children():
            self.tree.delete(i)
        # 后插入
        for user in self.user_manager.get_all_users():
            self.tree.insert('', tk.END, values=(user.username, user.role, user.status, user.address, user.phone))

    def approve_selected(self):
        '''
        批准选中的用户的注册申请
        '''
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请选择一个或多个待审批的用户。", parent=self)
            return
            
        approved_count = 0
        already_approved_or_admin = 0
        # 获取用户的申请状态
        for item in selected_items:
            values = self.tree.item(item, 'values')
            username = values[0]
            status = values[2]
            
            # 只处理 'pending' 状态的用户
            if status == 'pending':
                if self.user_manager.approve_user(username):
                    approved_count += 1
            else:
                already_approved_or_admin += 1
        
        if approved_count > 0:
            messagebox.showinfo("成功", f"{approved_count} 个用户的请求已被批准。", parent=self)
            self.refresh_users() # 刷新列表以显示更新后的状态
        elif already_approved_or_admin > 0 and approved_count == 0:
            messagebox.showinfo("提示", "所选用户已经是 'approved' 状态，无需批准。", parent=self)
        else:
            messagebox.showerror("错误", "批准用户时发生未知错误。", parent=self)

# --- 我的意向窗口 ---

class MyWantsWindow(tk.Toplevel):
    '''
    显示当前用户“想要”的物品列表
    '''
    def __init__(self, parent, items: List[Item]):
        super().__init__(parent)
        self.title("我的意向")
        self.geometry("600x400")
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ('name', 'category', 'price', 'status', 'owner', 'phone')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        tree.heading('name', text='物品名称')
        tree.heading('category', text='类别')
        tree.heading('price', text='原价')
        tree.heading('status', text='状态')
        tree.heading('owner', text='卖家')
        tree.heading('phone', text='联系电话')
        tree.pack(fill="both", expand=True)

        for item in items:
            status_text = "已售出" if item.status == 'sold' else "在售"
            tree.insert('', tk.END, values=(
                item.name, item.category, f"¥{item.price}", status_text, 
                item.owner_username, item.phone
            ))

# --- 有人想要窗口 ---

class ReceivedWantsWindow(tk.Toplevel):
    '''
    显示谁想要我的物品
    '''
    def __init__(self, parent, wants_data: List[Dict]):
        super().__init__(parent)
        self.title("有人想要")
        self.geometry("700x400")
        
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ('item_name', 'buyer_name', 'offer', 'phone', 'address')
        tree = ttk.Treeview(frame, columns=columns, show='headings')
        tree.heading('item_name', text='物品名称')
        tree.heading('buyer_name', text='买家')
        tree.heading('offer', text='买家出价')
        tree.heading('phone', text='联系电话')
        tree.heading('address', text='地址')
        
        tree.column('item_name', width=150)
        tree.column('address', width=200)
        tree.pack(fill="both", expand=True)

        for data in wants_data:
            offer_text = f"¥{data['offer_price']}" if data['offer_price'] > 0 else "-"
            tree.insert('', tk.END, values=(
                data['item_name'], data['buyer_name'], offer_text, 
                data['phone'], data['address']
            ))

# --- 买家选择窗口 ---

class BuyerSelectionWindow(tk.Toplevel):
    '''
    确认售出时选择买家的窗口
    '''
    def __init__(self, parent, wanters: List[User], callback):
        super().__init__(parent)
        self.title("选择买家")
        self.geometry("300x400")
        self.callback = callback
        self.wanters = wanters

        ttk.Label(self, text="请选择最终买家:", font=("", 10, "bold")).pack(pady=10)
        
        self.listbox = tk.Listbox(self)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        for user in wanters:
            self.listbox.insert(tk.END, f"{user.username} ({user.phone})")
            
        ttk.Button(self, text="确认", command=self.confirm).pack(pady=10)

    def confirm(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个买家。", parent=self)
            return
        self.callback(self.wanters[selection[0]])
        self.destroy()

# --- 物品详情视图 ---

class ItemDetailWindow(tk.Toplevel):
    '''
    物品详情窗口 (只读 + 留言板)
    '''
    def __init__(self, parent, item: Item, item_manager: ItemManager, current_user: User):
        super().__init__(parent)
        self.item = item
        self.item_manager = item_manager
        self.current_user = current_user
        self.title(f"物品详情 - {item.name}")
        self.geometry("400x500")
        
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding=20)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 辅助函数：添加一行信息
        def add_row(label, value):
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.pack(fill="x", pady=5)
            ttk.Label(row_frame, text=f"{label}:", font=("", 10, "bold"), width=15, anchor="w").pack(side="left")
            ttk.Label(row_frame, text=str(value), wraplength=250).pack(side="left", fill="x", expand=True)

        # 基本信息
        ttk.Label(scrollable_frame, text="基本信息", font=("", 12, "bold")).pack(anchor="w", pady=(0, 10))
        
        # --- 图片展示 ---
        if item.image_paths:
            try:
                img_path = item.image_paths[0]
                if os.path.exists(img_path):
                    pil_img = Image.open(img_path)
                    # 调整图片大小，最大宽度 300
                    pil_img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                    self.photo = ImageTk.PhotoImage(pil_img)
                    ttk.Label(scrollable_frame, image=self.photo).pack(anchor="w", pady=5)
            except Exception as e:
                print(f"加载图片失败: {e}")
        # ----------------

        add_row("物品名称", item.name)
        add_row("类别", item.category)
        add_row("价格", f"¥{item.price}")
        add_row("状态", "已售出" if item.status == 'sold' else ("在售" if item.want_count == 0 else f"{item.want_count}人想要"))
        add_row("可砍价", "是" if item.can_bargain else "否")
        add_row("交易地点", item.address)
        add_row("物品说明", item.description)

        # 联系人信息
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(scrollable_frame, text="卖家信息", font=("", 12, "bold")).pack(anchor="w", pady=(0, 10))
        add_row("发布者", item.owner_username)
        add_row("联系电话", item.phone)
        add_row("电子邮箱", item.email)

        # 特定属性
        if item.specific_attributes:
            ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=15)
            ttk.Label(scrollable_frame, text="详细属性", font=("", 12, "bold")).pack(anchor="w", pady=(0, 10))
            for k, v in item.specific_attributes.items():
                add_row(k, v)
        
        # --- 留言板区域 ---
        ttk.Separator(scrollable_frame, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(scrollable_frame, text="留言板", font=("", 12, "bold")).pack(anchor="w", pady=(0, 10))

        self.messages_frame = ttk.Frame(scrollable_frame)
        self.messages_frame.pack(fill="x", expand=True)

        # 输入区域
        input_frame = ttk.Frame(scrollable_frame)
        input_frame.pack(fill="x", pady=10)

        self.reply_to_label = ttk.Label(input_frame, text="", foreground="gray")
        self.reply_to_label.pack(anchor="w")
        self.reply_to_id = None

        input_row = ttk.Frame(input_frame)
        input_row.pack(fill="x")
        
        self.message_entry = ttk.Entry(input_row)
        self.message_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Button(input_row, text="发送", command=self.send_message).pack(side="left", padx=5)
        if self.current_user.username == self.item.owner_username:
             ttk.Button(input_row, text="取消回复", command=self.cancel_reply).pack(side="left")

        self.refresh_messages()

    def refresh_messages(self):
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
            
        messages = self.item_manager.get_messages(self.item.id)
        if not messages:
            ttk.Label(self.messages_frame, text="暂无留言，快来提问吧！", foreground="gray").pack(anchor="w", pady=5)
            return

        for msg in messages:
            frame = ttk.Frame(self.messages_frame)
            frame.pack(fill="x", pady=5)
            
            indent = 0
            prefix = ""
            if msg.reply_to_id:
                indent = 20
                prefix = "[回复] "
            
            # 头部: 发送者 + 时间
            header_text = f"{prefix}{msg.sender_name} ({msg.created_at}):"
            ttk.Label(frame, text=header_text, font=("", 9, "bold")).pack(anchor="w", padx=(indent, 0))
            
            # 内容
            ttk.Label(frame, text=msg.content, wraplength=350-indent).pack(anchor="w", padx=(indent, 0))
            
            # 回复按钮 (仅卖家可见)
            if self.current_user.username == self.item.owner_username:
                 ttk.Button(frame, text="回复", width=5, command=lambda m=msg: self.set_reply(m)).pack(anchor="e")

    def set_reply(self, message):
        self.reply_to_id = message.id
        self.reply_to_label.config(text=f"回复: {message.sender_name} - {message.content[:15]}...")
        self.message_entry.focus()

    def cancel_reply(self):
        self.reply_to_id = None
        self.reply_to_label.config(text="")
        
    def send_message(self):
        content = self.message_entry.get().strip()
        if not content:
            return
        
        self.item_manager.add_message(self.item.id, self.current_user.id, content, self.reply_to_id)
        self.message_entry.delete(0, tk.END)
        self.cancel_reply()
        self.refresh_messages()

# --- 主应用视图 ---

class ItemInfoWindow(tk.Toplevel):
    '''
    添加或修改物品的窗口
    '''
    def __init__(self, parent, item_manager: ItemManager, category_manager: CategoryManager, current_user: User, item_to_edit: Optional[Item] = None):
        super().__init__(parent)
        self.item_manager = item_manager
        self.category_manager = category_manager
        self.current_user = current_user
        self.item_to_edit = item_to_edit
        self.title("添加新物品" if not item_to_edit else "修改物品信息")
        self.selected_image_path = None
        
        self.common_entries: Dict[str, tk.Entry] = {}
        self.specific_entries: Dict[str, tk.Entry] = {}
        
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # 公有信息区
        common_frame = ttk.LabelFrame(main_frame, text="公共信息", padding=10)
        common_frame.pack(fill="x", pady=5)
        
        common_fields = ["物品名称", "物品说明", "价格", "交易地点"]
        for i, field in enumerate(common_fields):
            ttk.Label(common_frame, text=f"{field}:").grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(common_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            self.common_entries[field] = entry
        common_frame.columnconfigure(1, weight=1)

        # 是否可砍价
        ttk.Label(common_frame, text="接受砍价:").grid(row=len(common_fields), column=0, sticky="w", pady=2)
        self.bargain_combo = ttk.Combobox(common_frame, values=["是", "否"], state="readonly", width=38)
        self.bargain_combo.set("否")
        self.bargain_combo.grid(row=len(common_fields), column=1, sticky="ew", pady=2)

        # 类别选择
        ttk.Label(common_frame, text="物品类别:").grid(row=len(common_fields)+1, column=0, sticky="w", pady=2)
        self.category_combo = ttk.Combobox(common_frame, values=self.category_manager.get_all_categories(), state="readonly")
        self.category_combo.grid(row=len(common_fields)+1, column=1, sticky="ew")
        self.category_combo.bind("<<ComboboxSelected>>", self.on_category_change)
        
        # 图片上传
        ttk.Label(common_frame, text="物品图片:").grid(row=len(common_fields)+2, column=0, sticky="w", pady=2)
        img_frame = ttk.Frame(common_frame)
        img_frame.grid(row=len(common_fields)+2, column=1, sticky="ew", pady=2)
        ttk.Button(img_frame, text="选择图片...", command=self.select_image).pack(side="left")
        self.img_label = ttk.Label(img_frame, text="未选择", foreground="gray")
        self.img_label.pack(side="left", padx=5)
        
        # 特定属性区
        self.specific_frame = ttk.LabelFrame(main_frame, text="特定属性", padding=10)
        self.specific_frame.pack(fill="x", pady=5)

        # 保存按钮
        ttk.Button(main_frame, text="保存", command=self.save_item).pack(pady=10)

        # 如果是修改就改
        if self.item_to_edit:
            self.load_item_data()

    def select_image(self):
        path = filedialog.askopenfilename(title="选择图片", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if path:
            self.selected_image_path = path
            self.img_label.config(text=os.path.basename(path))

    def on_category_change(self, event=None):
        '''
        更新显示的类别
        '''
        # 清空旧的特定属性
        for widget in self.specific_frame.winfo_children():
            widget.destroy()
        self.specific_entries.clear()

        # 显示新的类别
        category = self.category_combo.get()
        attributes = self.category_manager.get_attributes_for_category(category)
        
        for i, attr in enumerate(attributes):
            ttk.Label(self.specific_frame, text=f"{attr}:").grid(row=i, column=0, sticky="w", pady=2)
            entry = ttk.Entry(self.specific_frame, width=40)
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            self.specific_entries[attr] = entry
        self.specific_frame.columnconfigure(1, weight=1)

    def load_item_data(self):
        '''
        装载物品数据
        '''
        item = self.item_to_edit
        self.common_entries["物品名称"].insert(0, item.name)
        self.common_entries["物品说明"].insert(0, item.description)
        self.common_entries["价格"].insert(0, str(item.price))
        self.common_entries["交易地点"].insert(0, item.address if item.address else "")
        self.bargain_combo.set("是" if item.can_bargain else "否")
        self.category_combo.set(item.category)
        self.on_category_change()               # 触发动态表单生成
        
        if item.image_paths:
            self.selected_image_path = item.image_paths[0]
            self.img_label.config(text=os.path.basename(self.selected_image_path))
        
        for attr, value in item.specific_attributes.items():
            if attr in self.specific_entries:
                self.specific_entries[attr].insert(0, value)
        
        self.category_combo.config(state="disabled") # 修改时不允许更改类别

        # 如果是新建，默认填入用户地址
        if not self.item_to_edit:
            self.common_entries["交易地点"].insert(0, self.current_user.address)

    def save_item(self):
        '''
        保存当前物品
        '''
        common_vals = {key: entry.get().strip() for key, entry in self.common_entries.items()}
        specific_vals = {key: entry.get().strip() for key, entry in self.specific_entries.items()}
        category = self.category_combo.get()
        
        if not all(common_vals.values()) or not category or not self.bargain_combo.get():
            messagebox.showerror("错误", "所有公共信息和类别都不能为空！", parent=self)
            return

        try:
            price = float(common_vals["价格"])
        except ValueError:
            messagebox.showerror("错误", "价格必须是数字！", parent=self)
            return
        
        can_bargain = 1 if self.bargain_combo.get() == "是" else 0
        
        image_paths = []
        if self.selected_image_path:
            # 检查是否是已有的图片（编辑模式下未修改图片）
            is_existing = False
            if self.item_to_edit and self.item_to_edit.image_paths:
                if os.path.abspath(self.selected_image_path) == os.path.abspath(self.item_to_edit.image_paths[0]):
                    is_existing = True
                    image_paths = [self.selected_image_path]
            
            if not is_existing:
                # 复制图片到本地 ITEM_IMG 文件夹，并重命名
                try:
                    ext = os.path.splitext(self.selected_image_path)[1]
                    new_filename = f"{uuid.uuid4().hex}{ext}"
                    target_path = os.path.join("ITEM_IMG", new_filename)
                    shutil.copy(self.selected_image_path, target_path)
                    image_paths = [target_path]
                except Exception as e:
                    messagebox.showerror("错误", f"保存图片失败: {e}", parent=self)
                    return
        
        # 如果是修改，准备需要更新的字段
        if self.item_to_edit: 
            update_data = {
                "name": common_vals["物品名称"],
                "description": common_vals["物品说明"],
                "price": price,
                "can_bargain": can_bargain,
                "address": common_vals["交易地点"],
                "image_paths": image_paths,
                "specific_attributes": specific_vals,
            }
            self.item_manager.revise_item(self.item_to_edit.item_id, update_data)
            messagebox.showinfo("成功", "物品修改成功！", parent=self)

        # 如果是创建，准备一个包含所有者和联系信息的完整数据包
        else: 
            item_data = {
                "name": common_vals["物品名称"],
                "description": common_vals["物品说明"],
                "price": price,
                "can_bargain": can_bargain,
                "address": common_vals["交易地点"],
                "phone": self.current_user.phone,
                "email": self.current_user.email,
                "category": category,
                "owner_username": self.current_user.username,
                "image_paths": image_paths,
                "specific_attributes": specific_vals
            }
            self.item_manager.create_item(**item_data)
            messagebox.showinfo("成功", "物品添加成功！", parent=self)
        
        # 统一的后续操作
        self.master.refresh_item_list()         # 调用父窗口的刷新方法
        self.destroy()


class MainView(ttk.Frame):
    '''
    主应用视图
    '''
    def __init__(self, parent, app_controller, current_user: User):
        super().__init__(parent)
        self.app_controller = app_controller
        self.current_user = current_user
        
        # 从控制器获取管理器实例
        self.user_manager = self.app_controller.user_manager
        self.item_manager = self.app_controller.item_manager
        self.category_manager = self.app_controller.category_manager

        self.grid(row=0, column=0, sticky="nsew")

        # 顶部操作区
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill="x")
        
        if self.current_user.role == 'user':
            ttk.Button(top_frame, text="添加物品", command=self.open_add_item_window).pack(side="left")
            
        ttk.Button(top_frame, text="修改选中", command=self.open_edit_item_window).pack(side="left", padx=5)
        ttk.Button(top_frame, text="删除选中", command=self.delete_selected_item).pack(side="left")
        
        if self.current_user.role == 'user':
            ttk.Button(top_frame, text="购买", command=self.buy_item).pack(side="left", padx=5)
            ttk.Button(top_frame, text="确认售出", command=self.confirm_sold).pack(side="left")
            ttk.Button(top_frame, text="我的意向", command=self.open_my_wants).pack(side="left", padx=5)
            ttk.Button(top_frame, text="有人想要", command=self.open_received_wants).pack(side="left")
            
        ttk.Button(top_frame, text="查看详情", command=self.open_item_details_window).pack(side="right")
        
        # 搜索区
        search_frame = ttk.LabelFrame(self, text="搜索物品", padding=10)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(search_frame, text="类别:").pack(side="left")
        self.search_category_combo = ttk.Combobox(search_frame, values=self.category_manager.get_all_categories(), state="readonly")
        self.search_category_combo.pack(side="left", padx=5)
        
        ttk.Label(search_frame, text="关键字:").pack(side="left")
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=5)
        
        ttk.Button(search_frame, text="搜索", command=self.search_items).pack(side="left")
        ttk.Button(search_frame, text="显示全部", command=self.refresh_item_list).pack(side="left", padx=5)

        # 物品列表区
        list_frame = ttk.Frame(self, padding=10)
        list_frame.pack(fill="both", expand=True)

        columns = ('id', 'name', 'category', 'price', 'status', 'bargain', 'owner')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('name', text='物品名称')
        self.tree.heading('category', text='类别')
        self.tree.heading('price', text='价格')
        self.tree.heading('status', text='状态')
        self.tree.heading('bargain', text='可砍价')
        self.tree.heading('owner', text='发布者')
        
        self.tree.column('id', width=40)
        self.tree.pack(fill="both", expand=True)
        
        # 配置列表颜色标记
        self.tree.tag_configure('sold', foreground='gray')      # 已售出: 灰色
        self.tree.tag_configure('wanted', foreground='red')     # 有人想要: 红色
        self.tree.tag_configure('active', foreground='green')   # 在售: 绿色
        
        self.refresh_item_list()

    def refresh_item_list(self, items: Optional[List[Item]] = None):
        '''
        更新显示的物品列表
        '''

        # 先清除
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # 读取所有的物品并写入
        item_source = items if items is not None else self.item_manager.get_all_items()
        for item in reversed(item_source):
            # 状态翻译
            tag = 'active'
            if item.status == 'sold':
                status_text = "已售出"
                tag = 'sold'
            else:
                if item.want_count == 0:
                    status_text = "在售"
                    tag = 'active'
                else:
                    status_text = f"{item.want_count}人想要"
                    tag = 'wanted'
            
            bargain_text = "是" if item.can_bargain else "否"
            
            self.tree.insert('', tk.END, values=(
                item.item_id, item.name, item.category, 
                f"¥{item.price}", status_text, bargain_text, item.owner_username
            ), tags=(tag,))
    
    def search_items(self):
        '''
        查找物品，必须选择一个类别
        '''
        category = self.search_category_combo.get()
        keyword = self.search_entry.get().strip()
        if not category:
            messagebox.showwarning("提示", "请先选择一个搜索类别。")
            return
        
        results = self.item_manager.search_items(category, keyword)
        self.refresh_item_list(results)     # 用查找到的物品更新显示的列表
        if not results:
            messagebox.showinfo("提示", "没有找到匹配的物品。")

    def open_add_item_window(self):
        if self.current_user.role == 'admin':
            messagebox.showinfo("提示", "管理员不能发布物品，仅用于管理系统。")
            return
        ItemInfoWindow(self, self.item_manager, self.category_manager, self.current_user)

    def open_edit_item_window(self):
        # 需要先选中要修改的物品
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请选择一个要修改的物品。")
            return
        
        item_id = int(self.tree.item(selected_items[0], 'values')[0])
        item_to_edit = self.item_manager.find_item_by_id(item_id)

        # 只有发布者或者管理员才能修改物品信息
        if item_to_edit.owner_username != self.current_user.username and self.current_user.role != 'admin':
            messagebox.showerror("错误", "您只能修改自己发布的物品。")
            return

        # 增加判断：已出售或有人想要的商品，非管理员不可修改
        if (item_to_edit.status == 'sold' or item_to_edit.want_count > 0) and self.current_user.role != 'admin':
            messagebox.showerror("权限限制", "该物品已售出或有人想要，无法修改。")
            return

        if item_to_edit:
            ItemInfoWindow(self, self.item_manager, self.category_manager, self.current_user, item_to_edit)
            
    def open_item_details_window(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择一个物品。")
            return
        
        item_id = int(self.tree.item(selected_items[0], 'values')[0])
        item = self.item_manager.find_item_by_id(item_id)
        if item:
            ItemDetailWindow(self, item, self.item_manager, self.current_user)

    def buy_item(self):
        '''普通用户购买物品'''
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择一个物品。")
            return
        
        item_id = int(self.tree.item(selected_items[0], 'values')[0])
        item = self.item_manager.find_item_by_id(item_id)
        
        if not item: return

        if item.owner_username == self.current_user.username:
            messagebox.showerror("错误", "您不能购买自己发布的物品。")
            return
        
        if item.status != 'active':
            messagebox.showerror("错误", "该物品当前不可购买（已被预定或已售出）。")
            return

        offer_price = 0.0
        if item.can_bargain:
            offer_price = simpledialog.askfloat("出价", f"该商品接受砍价 (原价: ¥{item.price})\n请输入您的出价:", parent=self, minvalue=0)
            if offer_price is None: # 用户取消
                return
        
        msg = f"确定想要购买 '{item.name}' 吗？"
        if offer_price > 0:
            msg += f"\n您的出价: ¥{offer_price}"

        if messagebox.askyesno("确认想要", msg + "\n卖家将看到您的意向。"):
            if self.item_manager.add_want(item.item_id, self.current_user.id, offer_price):
                messagebox.showinfo("成功", "已发送购买意向！")
                self.refresh_item_list()
            else:
                messagebox.showinfo("提示", "您已经添加过意向了。")

    def confirm_sold(self):
        '''卖家确认售出'''
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择一个物品。")
            return
        
        item_id = int(self.tree.item(selected_items[0], 'values')[0])
        item = self.item_manager.find_item_by_id(item_id)
        
        if not item: return

        if item.owner_username != self.current_user.username:
            messagebox.showerror("错误", "您只能确认自己发布的物品。")
            return
        
        if item.status == 'sold':
            messagebox.showerror("错误", "该物品已经售出。")
            return

        # 获取想要该物品的用户列表
        wanters = self.item_manager.get_item_wanters(item.item_id)
        
        if not wanters:
            messagebox.showinfo("提示", "目前还没有人想要这个物品，无法确认售出。")
            return

        def on_buyer_selected(buyer):
            if messagebox.askyesno("确认售出", f"确定将 '{item.name}' 卖给 {buyer.username} 吗？\n物品状态将变为'已售出'。"):
                self.item_manager.confirm_sold(item.item_id, buyer.id)
                messagebox.showinfo("成功", "操作成功！")
                self.refresh_item_list()

        BuyerSelectionWindow(self, wanters, on_buyer_selected)

    def open_my_wants(self):
        items = self.item_manager.get_user_wants(self.current_user.id)
        MyWantsWindow(self, items)

    def open_received_wants(self):
        wants_data = self.item_manager.get_received_wants(self.current_user.id)
        ReceivedWantsWindow(self, wants_data)

    def delete_selected_item(self):
        '''
        删除选中的物品
        '''
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请选择要删除的物品。")
            return
        
        if messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selected_items)} 个物品吗？"):
            for sel in selected_items:
                item_id = int(self.tree.item(sel, 'values')[0])
                item = self.item_manager.find_item_by_id(item_id)
                # 只有发布者或者管理员才能删除物品
                if item and (item.owner_username == self.current_user.username or self.current_user.role == 'admin'):
                    # 增加判断：已出售或有人想要的商品，非管理员不可删除
                    if (item.status == 'sold' or item.want_count > 0) and self.current_user.role != 'admin':
                        messagebox.showerror("权限限制", f"物品 '{item.name}' 已售出或有人想要，无法删除。")
                    else:
                        self.item_manager.delete_item(item_id)
                else:
                    messagebox.showerror("权限错误", f"您无权删除物品 '{item.name if item else '未知'}'。")
            
            self.refresh_item_list()    # 更新显示的列表

    def open_category_management(self):
        CategoryManagementWindow(self, self.category_manager)

    def open_user_management(self):
        UserManagementWindow(self, self.user_manager)