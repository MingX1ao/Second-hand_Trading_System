import logging
import pandas as pd
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
DATABASE_PATH = Path(r'database.xlsx')


# 存储单个物品信息的类
class Item():
    def __init__(self,
                 item_id: int,
                 item_name: str,
                 item_description: str,
                 contact_info: str,
                 valid: int = 1):
        '''
        Args:
            item_id: 物品id，自动生成，唯一，int
            item_name: 物品名称，str
            item_description: 物品描述，str
            contact_info: 联系人信息
            valid: 物品是否有效，=1有效，=0无效
        '''
        self.item_id: int = item_id
        self.item_name: str = item_name
        self.item_description: str = item_description
        self.contact_info: str = contact_info
        self.valid = valid

        logging.info(f'new item: {item_name}, created!')

    def to_dict(self):
        '''
        导出为字典，不包含valid
        '''
        return {
            'item id': self.item_id,
            'item name': self.item_name,
            'item description': self.item_description,
            'contact information': self.contact_info
        }

# 存储所有物品信息的表
class ItemTable():
    def __init__(self, db_path: Path = DATABASE_PATH):
        self.item_list: list[Item] = []         
        self.current_num: int = 0
        self.db_path = db_path
        self._init_db()
        self._load()

    def _init_db(self):
        '''
        如果数据库不存在就初始化一个
        '''
        if not self.db_path.exists():
            self.df = pd.DataFrame(columns=[
                'current num', 'item id', 'item name',
                'item description', 'contact information'
            ])
            self.df.to_excel(self.db_path, index=False)

    def _load(self):
        '''
        载入数据
        '''
        self.df = pd.read_excel(self.db_path)
        
        # 读取当前编号
        if not self.df.empty and 'current num' in self.df.columns and pd.notna(self.df.iloc[0]['current num']):
            self.current_num = int(self.df.iloc[0]['current num'])
        else:
            self.current_num = 0
        
        # 读取数据库，创建item
        self.item_list = []

        # 空表格，item_list保持空列表
        if self.df.empty:
            return  

        # 非空表格，逐行创建 Item
        for _, row in self.df.iterrows():
            self.item_list.append(Item(
                int(row['item id']),
                str(row['item name']),
                str(row['item description']),
                str(row['contact information']),
                valid=1  # 读入时都是有效的
            ))

    def create_new_item(self,
                        item_name: str,
                        item_description: str,
                        contact_info: str) -> None:
        '''
        Args:
            item_name: 物品名称，str
            item_description: 物品描述，str
            contact_info: 联系人信息
        '''
        self.current_num += 1
        logging.info(f'trying to create item with id: {self.current_num}')
        new_item = Item(self.current_num, item_name, item_description, contact_info)
        self.item_list.append(new_item)

        # 将新的一行写入数据库
        new_row = pd.DataFrame([{
            'current num': self.current_num,
            **new_item.to_dict()
        }])
        with pd.ExcelWriter(self.db_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
            new_row.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)


        # 后台日志
        logging.info(f'\t created an item with id: {new_item.item_id} \n'
                     f'\t item: {new_item.item_name}, {new_item.item_description} \n'
                     f'\t contact information is {new_item.contact_info} \n')

    # 修改物品信息
    def revise_item(self, 
                    item_id, 
                    name: str=None, 
                    description: str=None, 
                    contact: str=None):
        '''
        修改物品 → 原物品失效，新建一个继承相同id的有效物品
        Args:
            item_id:需要修改的物品id
            name: 修改后的物品名称
            description: 修改后的物品描述
            contact: 修改后的联系人信息
        '''
        logging.info(f'trying to revise item with id: {item_id} ...')
        for item in self.item_list:
            if item.item_id == item_id and item.valid == 1:
                item.valid = 0           # 标记旧物品无效

                # 创建新物品（继承 item_id）
                new_item = Item(
                    item_id=item.item_id,
                    item_name=name if name else item.item_name,
                    item_description=description if description else item.item_description,
                    contact_info=contact if contact else item.contact_info,
                    valid=1
                )
                self.item_list.append(new_item)

                # 新物品写入Excel
                new_row = pd.DataFrame([{
                    'current num': self.current_num,
                    **new_item.to_dict()
                }])
                with pd.ExcelWriter(self.db_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                    new_row.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)

                return new_item
        return None
    
    # 删除物品
    def delete_item(self, item_id: int) -> None:
        logging.info(f'trying to delete item with id: {item_id} ...')
        is_find = False
        for item in self.item_list:
            if item.item_id == item_id:
                item.valid = 0      # 逻辑删除，性能更强
                logging.info(f'item with id: {item_id} has been deleted!')
                is_find = True
                break
            else:
                continue
        
        if not is_find:
            logging.info(f'couldn\'t find item with id: {item_id}, please check it again!')

    # 显示物品列表
    def display_list(self, items: list[Item]=None) -> list[Item]:
        if list == None:
            logging.info(f'the following is the whole list of items:')
            for item in self.item_list:
                logging.info(f'\t item id: {item.item_id} \n'
                            f'\t item name: {item.item_name} \n'
                            f'\t item description: {item.item_description} \n'
                            f'\t contact information: {item.contact_info} \n')
            
        else:
            logging.info(f'the following is the specific list of items:')
            for item in items:
                logging.info(f'\t item id: {item.item_id} \n'
                            f'\t item name: {item.item_name} \n'
                            f'\t item description: {item.item_description} \n'
                            f'\t contact information: {item.contact_info} \n')
            
        return self.item_list if items is None else items

    # 查找物品信息
    def find_item(self, finding_info: str, finding_info_value) -> list[Item]:
        '''
        Args:
            finding_info: 用来查找物品的属性
            finding_info_value: 该属性的值
        '''
        logging.info(f'trying to find item with {finding_info}: {finding_info_value}...')
        if finding_info != 'item_id' and finding_info != 'item_name' and finding_info != 'item_description' and finding_info != 'contact_info':
            logging.info(f'{finding_info} is not a valid attribution, please check it again!')
            return None
        
        else:
            found_items = []
            for item in self.item_list:
                if finding_info == 'item_id' and item.item_id == finding_info_value:
                    found_items.append(item)
                elif finding_info == 'item_name' and finding_info_value in item.item_name:
                    found_items.append(item)
                elif finding_info == 'item_description' and finding_info_value in item.item_description:
                    found_items.append(item)
                elif finding_info == 'contact_info' and finding_info_value in item.contact_info:
                    found_items.append(item)
            if found_items == []:
                logging.info(f'find none items with specific attribution, try other keywords!')
                self.display_list()
            else:
                self.display_list(found_items)
                return found_items
    
    def get_all_items(self):
        '''
        获取当前有效的物品
        '''
        return [item for item in self.item_list if item.valid == 1]
        
    def save_and_close(self):
        '''
        关闭程序，只保存valid=1的物品
        '''
        valid_items = self.get_all_items()
        rows = [{
            'current num': self.current_num,
            **item.to_dict()
        } for item in valid_items]

        new_df = pd.DataFrame(rows)
        new_df.to_excel(self.db_path, index=False)
        print('数据已保存，程序关闭。')


if __name__ == '__main__':
    table = ItemTable()
    table.create_new_item('手机', '自用99新', '123456678')
    table.create_new_item('电脑', '二手8成新', '3142525')
    table.create_new_item('电脑', '坏了', '9812673861')
    table.display_list()

    # table.revise_item_attribution(2, 'item_name', '平板电脑')
    table.display_list()

    table.delete_item(1)
    table.delete_item(1)
    table.display_list()

    table.find_item('item', '平板电脑')
    table.find_item('item_name', '电脑')

