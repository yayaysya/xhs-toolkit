import asyncio
import sys
import os

# 将 'src' 目录添加到 Python 路径中，以便能够导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

try:
    from utils.image_processor import ImageProcessor
    from utils.logger import setup_logger, get_logger
except ImportError as e:
    print(f"导入模块失败，请确保您在项目的根目录下运行此脚本。错误: {e}")
    sys.exit(1)

# 配置日志记录器，我们只需要控制台输出
setup_logger(log_level="INFO", log_to_console=True, log_file=None)
logger = get_logger("FinalTestScript")

async def main():
    """
    最终测试脚本的主函数，用于顺序下载一组指定的图片URL。
    """
    image_urls = [
        "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/34012799e5834c7a80c03f9cad9bc875.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170847&x-signature=oj7oaGahBmNTymP%2F0UAfNuW9gnw%3D",
        "https://s.coze.cn/t/Wm_Dl1W0g_M/",
        "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/15bb6239cf394af0a35bd846753542dc.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170838&x-signature=Va3VDfX93ran4dqO0bGhgGLAUB0%3D",
        "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/4d76c09d87d84c1e9fa2899c39df508b.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170839&x-signature=H4V3PG2710eDFJDno97Ntgn8yBg%3D",
        "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/3c53572e4bc24d5daa89f14129a4bae5.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170838&x-signature=vDCF8%2BtpDqZxEKJYmZn%2BP%2FBRnG0%3D",
        "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/06c42092763045f5ba4ab44aa640aade.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170844&x-signature=jKaHAcq1k2p8VZR5YBaPZTjoVEc%3D",
        "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/02b5b7f286534483b15b060a0cdce360.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170843&x-signature=G4TAT6CdUmDmxUTxbzzRGxVgqFc%3D",
        "https://p26-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/c4627a834ebf4c578b4652395ccad061.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170850&x-signature=MIY351Mo1sY6pMpdHvJTV0kNGXY%3D",
        "https://p3-bot-workflow-sign.byteimg.com/tos-cn-i-mdko3gqilj/d978f630060a465289900ed585c8d43c.png~tplv-mdko3gqilj-image.png?rk3s=c8fe7ad5&x-expires=1783170856&x-signature=7NCzWbNjveMaN9bs%2FN1vemGZgXQ%3D"
    ]

    logger.info("--- 开始最终测试：顺序下载 ---")
    processor = ImageProcessor()
    
    try:
        downloaded_files = await processor.process_images(image_urls, strict_mode=True)
        logger.info("--- 测试结果 ---")
        logger.info(f"✅ 成功下载 {len(downloaded_files)}/{len(image_urls)} 张图片.")
        logger.info("下载的文件列表:")
        for f in downloaded_files:
            logger.info(f"- {f}")
    except Exception as e:
        logger.error("--- 测试结果 ---")
        logger.error(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 