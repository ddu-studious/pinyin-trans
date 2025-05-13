# Pinyin Reading Companion

## 注意事项

### PaddleSpeech 集成

当前已添加了PaddleSpeech策略的基本框架，但需要完成以下工作才能正常使用：

1. 安装依赖：
```bash
pip install paddlespeech  # 安装PaddleSpeech库
```

2. 模型下载：
- 访问[PaddleSpeech模型仓库](https://github.com/PaddlePaddle/PaddleSpeech)获取合适的中文语音模型
- 将模型放置在合适的位置（如models/paddlespeech）

3. 修改配置：
- 在app.py中设置环境变量PADDLE_SPEECH_MODEL_PATH指向模型文件
- 或者在PaddleSpeechTTSStrategy初始化时指定model_path参数

4. 实现具体功能：
- 根据PaddleSpeech文档完善PaddleSpeechTTSStrategy类中的模型加载和语音合成代码

5. 测试：
- 使用"paddlespeech"选项测试中文发音效果

6. 证书问题：
- 如果遇到证书验证问题，可能需要安装额外的CA证书
- 或者在请求时设置verify=False（不推荐用于生产环境）

// ... existing content ...