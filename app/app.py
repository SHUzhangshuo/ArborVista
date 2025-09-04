import os
import uuid
import json
import shutil
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import sys
from config import config

def allowed_file(filename, app):
    """检查文件格式是否允许"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    supported_extensions = {'pdf', 'png', 'jpg', 'jpeg'}
    return extension in supported_extensions

def process_file_with_mineru(input_path, output_dir, app, method='auto', backend='pipeline', language='ch'):
    """调用MinerU客户端处理文件"""
    try:
        # 检查文件格式
        file_path = Path(input_path)
        if not file_path.exists():
            return {'success': False, 'error': f'文件不存在: {input_path}'}
        
        # 检查文件扩展名
        supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        if file_path.suffix.lower() not in supported_extensions:
            return {
                'success': False, 
                'error': f'不支持的文件格式: {file_path.suffix}。支持的格式: {", ".join(supported_extensions)}'
            }
        
        # 验证MinerU模块是否可用
        try:
            # 添加当前项目路径到Python路径
            current_dir = Path(__file__).parent.parent
            if str(current_dir) not in sys.path:
                sys.path.insert(0, str(current_dir))
            
            import mineru.cli.client
            print("✅ MinerU模块导入成功")
        except ImportError as e:
            return {
                'success': False,
                'error': f'MinerU模块未安装或不可用: {str(e)}。请确保在正确的Python环境中运行。'
            }
        
        # 获取GPU配置 - 检测CUDA是否可用，智能选择设备模式
        try:
            import torch
            if torch.cuda.is_available():
                device_mode = os.environ.get('MINERU_DEVICE_MODE') or app.config.get('MINERU_CONFIG', {}).get('device_mode', 'cuda:0')
                print(f"✅ 检测到CUDA可用，使用GPU模式: {device_mode}")
                print(f"   GPU数量: {torch.cuda.device_count()}")
                print(f"   当前GPU: {torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else 'N/A'}")
            else:
                device_mode = 'cpu'
                print("⚠️ CUDA不可用，使用CPU模式")
        except ImportError:
            device_mode = 'cpu'
            print("⚠️ PyTorch未安装，使用CPU模式")
        except Exception as e:
            device_mode = 'cpu'
            print(f"⚠️ GPU检测失败: {e}，使用CPU模式")
        
        # 根据设备模式智能设置虚拟显存
        if device_mode.startswith('cuda'):
            try:
                import torch
                # 获取GPU显存信息
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
                virtual_vram = min(int(gpu_memory * 0.8), 8192)  # 使用80%显存，最大8GB
                print(f"   GPU显存: {gpu_memory:.1f}GB，设置虚拟显存: {virtual_vram}MB")
            except:
                virtual_vram = 7168  # 默认7GB
        else:
            virtual_vram = 1024  # CPU模式使用1GB
            print(f"   CPU模式，设置虚拟显存: {virtual_vram}MB")
        
        virtual_vram = os.environ.get('MINERU_VIRTUAL_VRAM_SIZE') or virtual_vram
        model_source = os.environ.get('MINERU_MODEL_SOURCE') or app.config.get('MINERU_CONFIG', {}).get('model_source', 'huggingface')
        
        # 构建命令 - 使用模块方式运行
        python_exe = sys.executable
        print(f"🐍 使用Python解释器: {python_exe}")
        
        # 使用Python -c 方式直接调用，确保能找到mineru模块
        # 转义路径中的反斜杠
        current_dir_escaped = str(current_dir).replace('\\', '\\\\')
        input_path_escaped = str(input_path).replace('\\', '\\\\')
        output_dir_escaped = str(output_dir).replace('\\', '\\\\')
        
        cmd = [
            python_exe, '-c',
            f'''
import sys
sys.path.insert(0, r"{current_dir}")
import mineru.cli.client
import sys
sys.argv = [
    "mineru.cli.client",
    "-p", r"{input_path}",
    "-o", r"{output_dir}",
    "-m", "{method}",
    "-b", "{backend}",
    "-l", "{language}",
    "-d", "{device_mode}",
    "--vram", "{virtual_vram}",
    "--source", "{model_source}"
]
mineru.cli.client.main()
'''
        ]
        
        print(f"🚀 MinerU 处理配置:")
        print(f"   📁 输入文件: {input_path}")
        print(f"   📁 输出目录: {output_dir}")
        print(f"   📱 设备模式: {device_mode}")
        print(f"   💾 GPU内存: {virtual_vram}MB")
        print(f"   📦 模型源: {model_source}")
        print(f"   🔧 处理方法: {method}")
        print(f"   🔧 后端: {backend}")
        print(f"   🌐 语言: {language}")
        print(f"执行命令: {' '.join(cmd)}")
        print(f"工作目录: {app.config['BASE_DIR'].parent}")
        
        # 执行命令
        # 设置环境变量确保使用正确的Python路径和设备模式
        env = os.environ.copy()
        current_pythonpath = env.get('PYTHONPATH', '')
        if current_pythonpath:
            env['PYTHONPATH'] = f"{str(app.config['BASE_DIR'].parent)};{current_pythonpath}"
        else:
            env['PYTHONPATH'] = str(app.config['BASE_DIR'].parent)
        
        # 强制设置设备模式环境变量
        env['MINERU_DEVICE_MODE'] = device_mode
        env['MINERU_VIRTUAL_VRAM_SIZE'] = str(virtual_vram)
        env['MINERU_MODEL_SOURCE'] = model_source
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(current_dir),  # 使用当前项目目录
            timeout=300,  # 5分钟超时
            env=env
        )
        
        print(f"命令返回码: {result.returncode}")
        print(f"标准输出: {result.stdout}")
        print(f"标准错误: {result.stderr}")
        
        if result.returncode == 0:
            return {'success': True}
        else:
            # 解析错误信息
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = result.stdout.strip()
            if not error_msg:
                error_msg = f"处理失败，返回码: {result.returncode}"
            
            return {
                'success': False,
                'error': f'处理失败: {error_msg}'
            }
    except subprocess.TimeoutExpired:
        print(f"处理超时: {input_path}")
        return {
            'success': False,
            'error': '文件处理超时，请尝试较小的文件'
        }
    except Exception as e:
        print(f"执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': f'执行失败: {str(e)}'
        }

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    config_class = config[config_name]
    config_class.init_app(app)
    
    # 将配置项添加到app.config中
    for key in dir(config_class):
        if not key.startswith('_') and not callable(getattr(config_class, key)):
            app.config[key] = getattr(config_class, key)
    
    # 启用CORS
    CORS(app)
    
    # 注册路由
    register_routes(app)
    
    return app

def register_routes(app):
    """注册应用路由"""
    
    @app.route('/api/upload', methods=['POST'])
    def upload_file():
        """处理文件上传"""
        try:
            print(f"开始处理文件上传...")
            
            if 'file' not in request.files:
                return jsonify({'error': '没有文件'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': '没有选择文件'}), 400
            
            print(f"上传文件: {file.filename}")
            
            # 检查文件格式
            if not allowed_file(file.filename, app):
                return jsonify({'error': f'不支持的文件格式: {file.filename}。支持的格式: PDF, PNG, JPG, JPEG'}), 400
            
            # 获取用户选择的配置参数
            method = request.form.get('method', 'auto')
            backend = request.form.get('backend', 'pipeline')
            language = request.form.get('language', 'ch')
            
            # 生成唯一ID
            file_id = str(uuid.uuid4())
            
            # 创建目录
            input_file_dir = app.config['INPUT_DIR']
            output_file_dir = app.config['OUTPUT_DIR'] / file_id
            output_file_dir.mkdir(exist_ok=True)
            
            # 保存文件
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            new_filename = f"{file_id}.{file_extension}" if file_extension else file_id
            file_path = input_file_dir / new_filename
            input_file_dir.mkdir(parents=True, exist_ok=True)
            file.save(str(file_path))
            
            # 调用MinerU客户端处理文件
            try:
                print("开始调用MinerU客户端...")
                result = process_file_with_mineru(str(file_path), str(output_file_dir), app, method, backend, language)
                if result['success']:
                    print("文件处理成功")
                    return jsonify({
                        'success': True,
                        'file_id': file_id,
                        'filename': file.filename,
                        'message': '文件处理成功'
                    })
                else:
                    print(f"文件处理失败: {result['error']}")
                    return jsonify({'error': result['error']}), 500
            except Exception as e:
                print(f"文件处理异常: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'文件处理失败: {str(e)}'}), 500
                
        except Exception as e:
            print(f"上传处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'上传失败: {str(e)}'}), 500

    @app.route('/api/files', methods=['GET'])
    def get_files():
        """获取所有已处理的文件列表"""
        try:
            files = []
            output_dir = app.config['OUTPUT_DIR']
            
            # 遍历output目录下的UUID子目录
            for output_subdir in output_dir.iterdir():
                if output_subdir.is_dir():
                    # 查找markdown文件 - 在file_id/file_id/auto子目录中
                    md_files = list((output_subdir / output_subdir.name / "auto").glob("*.md"))
                    if md_files:
                        # 获取原始文件名（去掉扩展名）
                        md_file = md_files[0]
                        filename = md_file.stem.replace('_', ' ').replace('-', ' ')
                        
                        files.append({
                            'id': output_subdir.name,
                            'filename': filename,
                            'created_at': md_file.stat().st_ctime
                        })
            
            # 按创建时间排序
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return jsonify({'files': files})
            
        except Exception as e:
            return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>/content', methods=['GET'])
    def get_file_content(file_id):
        """获取指定文件的markdown内容"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            
            # 根据file_id构建目录路径
            output_subdir = output_dir / file_id
            if not output_subdir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            # 查找markdown文件 - 在file_id/file_id/auto子目录中
            md_files = list((output_subdir / file_id / "auto").glob("*.md"))
            if not md_files:
                return jsonify({'error': '未找到markdown文件'}), 404
            
            md_file = md_files[0]
            print(f"找到markdown文件: {md_file}")
            
            # 读取markdown内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 处理图片路径，将相对路径转换为API路径
            import re
            
            # 查找所有图片引用
            # 匹配 ![alt](path) 格式
            image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
            
            def replace_image_path(match):
                alt_text = match.group(1)
                image_path = match.group(2)
                
                print(f"处理图片路径: {image_path}")
                
                                # 如果路径是相对路径，转换为API路径
                if not image_path.startswith(('http://', 'https://', '/')): 
                    # 获取API基础URL，优先使用环境变量，否则使用localhost
                    api_base_url = os.environ.get('API_BASE_URL', 'http://localhost:5000')
                    # 如果路径已经包含images目录，直接使用文件名
                    if image_path.startswith('images/'):
                        filename = image_path.replace('images/', '')
                        api_path = f"{api_base_url}/api/files/{file_id}/images/{filename}"
                        print(f"路径已包含images目录，转换为完整API路径: {api_path}")
                        return f'![{alt_text}]({api_path})'
                    else:
                        # 构建完整的API路径
                        api_path = f"{api_base_url}/api/files/{file_id}/images/{image_path}"
                        print(f"转换为完整API路径: {api_path}")
                        return f'![{alt_text}]({api_path})'
                else:
                    # 保持原有路径不变
                    print(f"保持原有路径: {image_path}")
                    return match.group(0)
            
            # 替换图片路径
            content = re.sub(image_pattern, replace_image_path, content)
            
            # 直接保留HTML表格，让markdown-it渲染
            print(f"处理后的内容预览: {content[:1000]}...")
            
            # 检查是否包含表格
            if '<table' in content:
                print("✅ 检测到HTML表格内容")
                table_matches = re.findall(r'<table.*?</table>', content, re.DOTALL)
                print(f"HTML表格数量: {len(table_matches)}")
                for i, table in enumerate(table_matches[:2]):  # 显示前2个表格
                    print(f"HTML表格 {i+1}: {table[:200]}...")
            else:
                print("❌ 未检测到HTML表格内容")
            
            # 获取文件名
            filename = md_file.stem.replace('_', ' ').replace('-', ' ')
            
            return jsonify({
                'content': content,
                'filename': filename,
                'file_id': file_id
            })
            
        except Exception as e:
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>/images/<path:image_path>')
    def get_image(file_id, image_path):
        """获取图片文件"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            
            # 图片文件在 file_id/file_id/auto/images 子目录中
            image_file = output_dir / file_id / file_id / "auto" / "images" / image_path
            
            print(f"查找图片文件: {image_file}")
            print(f"文件是否存在: {image_file.exists()}")
            
            if not image_file.exists():
                # 尝试列出目录内容，帮助调试
                parent_dir = image_file.parent
                if parent_dir.exists():
                    print(f"父目录存在，内容: {list(parent_dir.iterdir())}")
                else:
                    print(f"父目录不存在: {parent_dir}")
                return jsonify({'error': '图片不存在'}), 404
            
            print(f"找到图片文件: {image_file}")
            return send_from_directory(str(image_file.parent), image_path)
            
        except Exception as e:
            print(f"获取图片异常: {str(e)}")
            return jsonify({'error': f'获取图片失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>', methods=['DELETE'])
    def delete_file(file_id):
        """删除指定文件"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            input_dir = app.config['INPUT_DIR']
            
            # 删除输出目录（UUID子目录）
            output_subdir = output_dir / file_id
            if output_subdir.exists():
                shutil.rmtree(output_subdir)
            
            # 删除输入文件（UUID命名的文件）
            # 查找对应的输入文件
            for input_file in input_dir.iterdir():
                if input_file.is_file() and input_file.stem == file_id:
                    input_file.unlink()
                    break
            
            return jsonify({'message': '删除成功'})
            
        except Exception as e:
            return jsonify({'error': f'删除失败: {str(e)}'}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        """健康检查接口"""
        return jsonify({
            'status': 'healthy',
            'app_name': app.config['APP_NAME'],
            'version': app.config['APP_VERSION']
        })

    @app.route('/api/config/options', methods=['GET'])
    def get_config_options():
        """获取配置选项接口"""
        return jsonify({
            'methods': ['auto', 'txt', 'ocr'],
            'languages': ['ch', 'ch_server', 'ch_lite', 'en', 'korean', 'japan', 'chinese_cht', 'ta', 'te', 'ka',
                         'latin', 'arabic', 'east_slavic', 'cyrillic', 'devanagari'],
            'defaults': {
                'method': 'auto',
                'language': 'ch'
            }
        })

# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='localhost', port=5000)