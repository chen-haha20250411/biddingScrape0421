import concurrent.futures
import logging
from importlib import import_module

# 配置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 要运行的脚本列表
SCRIPTS = [
    'get_GuoJi',
    'get_sun',
    'get_xunbiaowang'
]

def run_script(script_name):
    """运行单个脚本"""
    try:
        module = import_module(script_name)
        # 直接调用 scrape_data() 方法
        if hasattr(module, 'scrape_data'):
            module.scrape_data()
        else:
            logging.error(f"{script_name} 没有找到 scrape_data 方法")
    except Exception as e:
        logging.error(f"运行 {script_name} 时出错: {e}")

def main():
    """主程序入口"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有脚本任务
        future_to_script = {
            executor.submit(run_script, script): script 
            for script in SCRIPTS
        }
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(future_to_script):
            script = future_to_script[future]
            try:
                future.result()
                logging.info(f"{script} 执行完成")
            except Exception as e:
                logging.error(f"{script} 执行出错: {e}")

if __name__ == "__main__":
    main()