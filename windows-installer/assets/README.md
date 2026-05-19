# 图标占位说明

最终安装包需要一个图标文件：`windows-installer/assets/icon.ico`

要求：
- ICO 格式（Windows 原生）
- 建议包含 16×16、32×32、48×48、256×256 多尺寸
- 透明背景

获取方法（任选其一）：
1. 设计师出图，导出为 multi-resolution .ico
2. 用 https://icoconvert.com/ 把一张 PNG 转 .ico
3. 暂时随便扔一个 .ico 进来，构建脚本不会因为缺图标失败（但安装包外观会很丑）

如果完全不放，PyInstaller 会用默认图标，Inno Setup 编译会报错——`SetupIconFile` 是必填项。
临时方案：把任意 .ico 文件复制成 `icon.ico` 即可继续。
