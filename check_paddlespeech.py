import os
import sys
from pathlib import Path

# 检查环境变量
print('检查PaddleSpeech环境变量:')
print('PADDLE_SPEECH_MODEL_PATH:', os.environ.get('PADDLE_SPEECH_MODEL_PATH'))
print('当前工作目录:', os.getcwd())

# 检查模型文件是否存在
model_path = os.path.join(os.getcwd(), 'models/paddlespeech/G2PWModel_1.1.zip')
print('本地模型路径:', model_path)
print('模型文件存在:', os.path.exists(model_path))

# 尝试导入PaddleSpeech并检查其配置
try:
    from paddlespeech.resource import pretrained_models
    print('\nPaddleSpeech模型配置信息:')
    
    # 查找G2P相关模型配置
    g2p_models = [m for m in dir(pretrained_models) if 'G2P' in m]
    print('G2P相关配置项:', g2p_models)
    
    # 检查预训练模型主目录设置
    pretrained_home = getattr(pretrained_models, 'PRETRAINED_MODELS_HOME', None)
    print('预训练模型主目录:', pretrained_home)
    
    # 检查下载函数
    if hasattr(pretrained_models, 'download_and_decompress'):
        download_func = pretrained_models.download_and_decompress
        print('\n下载函数参数信息:')
        print(download_func.__doc__)
        
    # 尝试查找G2P模型的具体配置
    if hasattr(pretrained_models, 'MODEL_HOME'):
        print('\nMODEL_HOME:', pretrained_models.MODEL_HOME)
    
    # 检查是否有禁用下载的选项
    print('\n可能的禁用下载选项:')
    disable_options = [attr for attr in dir(pretrained_models) if 'DISABLE' in attr or 'NO_DOWNLOAD' in attr]
    print(disable_options if disable_options else '未找到明确的禁用下载选项')
    
    # 检查paddlespeech.cli.g2p模块
    try:
        from paddlespeech.cli.g2p import g2p_executor
        print('\nG2P执行器配置:')
        executor = g2p_executor.G2PExecutor()
        print('模型类型:', executor.model_type)
        print('使用本地模型:', getattr(executor, 'use_local_model', '未找到该属性'))
    except Exception as e:
        print(f'导入G2P执行器失败: {e}')
        
except ImportError as e:
    print(f'\n导入PaddleSpeech失败: {e}')
except Exception as e:
    print(f'\n检查PaddleSpeech配置时出错: {e}')