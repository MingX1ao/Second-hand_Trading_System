import tkinter as tk
from tkinter import ttk, messagebox
from models import UserManager, ItemManager, CategoryManager
from gui_components import LoginView, MainView, CreateAdminView

class App(tk.Tk):
    '''
    主应用控制器
    '''
    def __init__(self):
        super().__init__()
        
        # 初始化数据管理器
        self.user_manager = UserManager()
        self.item_manager = ItemManager()
        self.category_manager = CategoryManager()

        self.current_user = None
        self._current_view = None

        # 配置主窗口, 初始为登录窗口大小
        self.title("二手物品交易系统")
        self.geometry("350x200")

        # 创建一个容器来放置视图
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)

        # 检查是否需要初始化管理员
        if not self.user_manager.has_admin():
            self.show_create_admin_view()
        else:
            self.show_login_view()

    def _switch_view(self, View, **kwargs):
        '''
        通用视图切换方法
        '''
        # 先清除当前视图
        if self._current_view:
            self._current_view.destroy()
        
        # 再创建新的视图
        self._current_view = View(self.container, self, **kwargs)

    def show_create_admin_view(self):
        '''
        显示创建管理员界面
        '''
        self.title("系统初始化 - 创建管理员")
        self.geometry("400x300")
        self._switch_view(CreateAdminView)

    def show_login_view(self):
        '''
        显示登录界面
        '''
        self.title("登录 - 二手物品交易系统")
        self.geometry("350x200")
        self.config(menu=tk.Menu(self))             # 清空菜单栏
        self._switch_view(LoginView)                # 展示登录界面

    def show_main_view(self):
        '''
        登录成功后显示主界面
        '''
        self.title(f"二手物品交易系统 - 欢迎, {self.current_user.username} ({self.current_user.role})")
        self.geometry("800x600")
        self.create_main_menu()                     # 创建主菜单
        self._switch_view(MainView, current_user=self.current_user)

    def attempt_login(self, username, password):
        '''
        处理登录逻辑
        '''
        # 先检查用户是否存在
        if not self.user_manager.get_user(username):
            messagebox.showerror("登录失败", "用户不存在。")
            return

        user = self.user_manager.authenticate(username, password)       # 将登陆信息与数据库中信息进行对比
        # 如果对上了且用户已被批准
        if user and user.status == 'approved':
            self.current_user = user
            self.show_main_view()       # 切换到主界面
        # 如果对上了但是用户还在审批
        elif user and user.status == 'pending':
            messagebox.showwarning("登录失败", "您的账户正在等待管理员审批。")
        # 信息对不上
        else:
            messagebox.showerror("登录失败", "密码错误。")
    
    def logout(self):
        '''
        处理退出登录逻辑
        '''
        self.current_user = None
        self.show_login_view()
    
    def create_main_menu(self):
        '''
        创建主窗口的菜单栏
        '''
        menubar = tk.Menu(self)
        
        # 开始菜单, 所有用户可见
        start_menu = tk.Menu(menubar, tearoff=0)
        start_menu.add_command(label="退出登录", command=self.logout)
        start_menu.add_separator()
        start_menu.add_command(label="退出程序", command=self.quit)
        menubar.add_cascade(label="开始", menu=start_menu)

        # 管理菜单, 仅管理员可见
        if self.current_user and self.current_user.role == 'admin':
            admin_menu = tk.Menu(menubar, tearoff=0)
            admin_menu.add_command(label="类别管理", command=lambda: self._current_view.open_category_management())
            admin_menu.add_command(label="用户管理", command=lambda: self._current_view.open_user_management())
            menubar.add_cascade(label="管理", menu=admin_menu)
        
        # 配置菜单栏
        self.config(menu=menubar)

if __name__ == '__main__':
    app = App()
    app.mainloop()