"""
下载Embedding模型到指定目录
用于预先下载模型，避免运行时下载
"""

import os
import sys
from pathlib import Path

def download_model(model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", 
                   target_dir: str = None):
    """
    下载HuggingFace模型到指定目录
    
    Args:
        model_name: 模型名称
        target_dir: 目标目录，如果为None则使用默认路径
    """
    # 设置目标目录
    if target_dir is None:
        base_dir = Path(__file__).parent.parent
        target_dir = base_dir / "data" / "vectorDatabase" / "models"
    else:
        target_dir = Path(target_dir)
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("📦 下载Embedding模型")
    print("=" * 60)
    print(f"📁 模型保存目录: {target_dir}")
    print(f"🤖 模型名称: {model_name}")
    print("-" * 60)
    
    # 设置环境变量
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(target_dir)
    os.environ['HF_HOME'] = str(target_dir)
    
    try:
        print("\n🔄 正在下载模型（首次下载可能需要几分钟）...")
        print("   请确保网络连接正常，模型大小约400MB")
        
        # 导入sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            print("\n❌ 错误: 未安装 sentence-transformers")
            print("   请运行: pip install sentence-transformers")
            return False
        
        # 下载并加载模型
        model = SentenceTransformer(model_name, cache_folder=str(target_dir))
        
        # 测试模型
        print("\n🧪 测试模型...")
        test_text = "这是一个测试文本"
        embedding = model.encode(test_text)
        
        if embedding is None or len(embedding) == 0:
            print("❌ 模型测试失败")
            return False
        
        print(f"✅ 模型测试成功，向量维度: {len(embedding)}")
        print(f"\n✅ 模型下载完成！")
        print(f"📦 模型已保存到: {target_dir}")
        
        # 显示模型文件
        print("\n📂 模型文件:")
        model_files = list(target_dir.glob("**/*"))
        for file in sorted(model_files)[:10]:  # 只显示前10个文件
            if file.is_file():
                size = file.stat().st_size / (1024 * 1024)  # MB
                print(f"   - {file.name} ({size:.2f} MB)")
        
        if len(model_files) > 10:
            print(f"   ... 还有 {len(model_files) - 10} 个文件")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 下载失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="下载Embedding模型")
    parser.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        help="模型名称 (默认: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="目标目录 (默认: data/vectorDatabase/models)"
    )
    
    args = parser.parse_args()
    
    success = download_model(
        model_name=args.model,
        target_dir=args.dir
    )
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 模型下载完成！现在可以在RAG系统中使用了")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 模型下载失败，请检查错误信息")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

