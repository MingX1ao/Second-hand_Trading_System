from items import ItemTable
import tkinter as tk
from tkinter import ttk, messagebox

# GUI部分
class ItemManagerGUI:
    def __init__(self, root: tk.Tk, table: ItemTable):
        '''
        Args:
            root: tk的顶部窗口
            table: 维护的物品列表
        '''
        self.root = root
        self.table = table
        self.root.title('二手物品交易系统')

        self.current_edit_id = None    # 当前选中的 item_id

        # 保存上一个状态
        self.ori_name = None
        self.ori_desc = None
        self.ori_contact = None

        # 上方输入区
        frame_input = tk.Frame(self.root)
        frame_input.pack(padx=10, pady=5, fill='x')

        tk.Label(frame_input, text='物品名称:').grid(row=0, column=0, sticky='w')
        self.entry_name = tk.Entry(frame_input, width=30)
        self.entry_name.grid(row=0, column=1, sticky='we')

        tk.Label(frame_input, text='物品描述:').grid(row=1, column=0, sticky='w')
        self.entry_desc = tk.Entry(frame_input, width=30)
        self.entry_desc.grid(row=1, column=1, sticky='we')

        tk.Label(frame_input, text='联系人信息:').grid(row=2, column=0, sticky='w')
        self.entry_contact = tk.Entry(frame_input, width=30)
        self.entry_contact.grid(row=2, column=1, sticky='we')
        
        # 清空输入框
        tk.Button(frame_input, text='清空输入框', command=self.clear_inputs).grid(row=1, column=2, pady=5)

        # 三个操作的按钮
        tk.Button(frame_input, text='添加物品', command=self.add_item).grid(row=3, column=0, pady=5)
        tk.Button(frame_input, text='删除选中物品', command=self.delete_item).grid(row=3, column=1, pady=5)
        tk.Button(frame_input, text='修改选中物品', command=self.revise_item).grid(row=3, column=2, pady=5)

        # 中间列表区
        frame_list = tk.Frame(self.root)
        frame_list.pack(padx=10, pady=5, fill='both', expand=True)

        columns = ('id', 'name', 'desc', 'contact')
        self.tree = ttk.Treeview(frame_list, columns=columns, show='headings')
        self.tree.heading('id', text='物品ID')
        self.tree.heading('name', text='物品名称')
        self.tree.heading('desc', text='物品描述')
        self.tree.heading('contact', text='联系人信息')

        self.tree.column('id', width=50)
        self.tree.column('name', width=120)
        self.tree.column('desc', width=180)
        self.tree.column('contact', width=150)

        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)      # 绑定选择事件：选中一行就把字段数据放到输入框里

        # 下方查找区
        frame_search = tk.Frame(self.root)
        frame_search.pack(padx=10, pady=5, fill='x')

        tk.Label(frame_search, text='搜索关键字:').grid(row=0, column=0, sticky='w')
        self.entry_search = tk.Entry(frame_search)
        self.entry_search.grid(row=0, column=1, sticky='we')

        # 查找的选项
        self.combo_field = ttk.Combobox(frame_search, values=['item id', 'item name', 'item description', 'contact information'])
        self.combo_field.set('')
        self.combo_field.grid(row=0, column=2, padx=5)

        tk.Button(frame_search, text='查找', command=self.search_item).grid(row=0, column=3, padx=5)
        tk.Button(frame_search, text='显示全部', command=self.refresh_list).grid(row=0, column=4, padx=5)

        frame_search.columnconfigure(1, weight=1)

        self.refresh_list()

    def add_item(self):
        '''
        添加二手物品
        '''
        # 获取输入内容
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()
        contact = self.entry_contact.get().strip()
        if not name or not desc or not contact:
            messagebox.showwarning('警告', '任何物品属性均不能为空！')
            return
        if self.entry_name.get().strip() == self.ori_name and self.entry_desc.get().strip() == self.ori_desc and self.entry_contact.get().strip() == self.ori_contact:
            messagebox.showinfo('警告', '请勿连续输入相同的信息')
            return
        
        # 创建物品，更新显示列表
        self.table.create_new_item(name, desc, contact)
        self.refresh_list()
        self.clear_inputs()

    def delete_item(self):
        '''
        删除物品，支持批量删除
        '''
        selected = self.tree.selection()    # 选中物品
        if not selected:
            messagebox.showinfo('提示', '请先选中要删除的物品')
            return
        for sel in selected:
            item_id = int(self.tree.item(sel, 'values')[0])
            self.table.delete_item(item_id)     # 删除物品
       
        # 更新显示列表
        self.refresh_list()
        self.clear_inputs()

    def revise_item(self):
        '''
        修改特定属性
        '''
        # 首先先选中一个物品
        if self.current_edit_id is None:
            messagebox.showinfo('提示', '请先选中要修改的物品')
            return
        
        # 获取输入字段
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip()
        contact = self.entry_contact.get().strip()

        # 全都一致就提示
        if (name == self.ori_name and desc == self.ori_desc and contact == self.ori_contact):
            messagebox.showinfo('提示', '当前信息未更改, 请至少修改一项')
            return
            
        # 修改信息
        self.table.revise_item(self.current_edit_id, name=name, description=desc, contact=contact)
        messagebox.showinfo('提示', '修改成功')
        self.refresh_list()
        self.clear_inputs()

    def search_item(self):
        '''
        查找物品，支持模糊查找
        '''
        keyword = self.entry_search.get().strip()
        field = self.combo_field.get()
        if not keyword:
            messagebox.showwarning('警告', '请输入搜索关键字')
            return
        
        found = []
        for item in self.table.item_list:
            
            # 对于记为0的不用管
            if not item.valid:
                continue

            if field == 'item id':
                # 输入必须是整型
                if item.item_id == int(keyword):
                    found.append(item)
                else:
                    messagebox.showinfo('警告', '按id查找时必须输入整数')
            elif field == 'item name' and keyword in item.item_name:
                found.append(item)
            elif field == 'item description' and keyword in item.item_description:
                found.append(item)
            elif field == 'contact information' and keyword in item.contact_info:
                found.append(item)
        if not found:
            messagebox.showinfo('提示', '没有找到匹配的物品')
            # 显示全部的物品
            self.refresh_list()
        else:
            self.refresh_list(found)

    def on_select(self, event):
        '''
        当选中列表里的某行时，把值填到输入框里
        '''
        selected = self.tree.selection()
        if not selected:
            return
        values = self.tree.item(selected[0], 'values')
        self.current_edit_id = int(values[0])

        # 删除输入框中原有字段，再填入选中的物品的字段
        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, values[1])
        self.entry_desc.delete(0, tk.END)
        self.entry_desc.insert(0, values[2])
        self.entry_contact.delete(0, tk.END)
        self.entry_contact.insert(0, values[3])

        # 保存上次状态，用于和输入比较
        self.ori_name = self.entry_name.get().strip()
        self.ori_desc = self.entry_desc.get().strip()
        self.ori_contact = self.entry_contact.get().strip()

    def clear_inputs(self):
        '''
        清空输入框和当前编辑ID
        '''
        self.entry_name.delete(0, tk.END)
        self.entry_desc.delete(0, tk.END)
        self.entry_contact.delete(0, tk.END)
        self.current_edit_id = None

    def refresh_list(self, items=None):
        '''
        每次操作后更新列表
        '''
        # 先对清空当前显示的列表
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        # 然后对显示列表进行更新
        if items is None:       # 用于没有查找到符合条件的物品时
            items = self.table.get_all_items()      # 只显示valid=1的
        for item in items[::-1]:
            self.tree.insert('', tk.END, values=(item.item_id, item.item_name, item.item_description, item.contact_info))




if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    table = ItemTable()

    root = tk.Tk()
    gui = ItemManagerGUI(root, table)
    root.mainloop()
    table.save_and_close()
