from flask import Blueprint, render_template, request, jsonify, send_file
import os

main = Blueprint('main', __name__)

@main.route('/test')
def test():
    """
    路由测试接口
    """
    return "路由测试成功", 200

from tts_strategies import tts_strategies  # 修改: 直接从 tts_strategies 模块导入


@main.route('/engines')
def get_engines():
    """
    获取可用的TTS引擎列表
    """
    return jsonify(list(tts_strategies.keys()))  # 强制返回 JSON 格式
