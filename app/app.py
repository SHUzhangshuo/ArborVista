import os
import uuid
import json
import shutil
import traceback
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_cors import CORS
from config import config
from mineru_api import MinerUAPI
import sys

# 添加agent目录到路径
agent_dir = Path(__file__).parent.parent / "agent"
sys.path.insert(0, str(agent_dir))

def allowed_file(filename, app):
    """检查文件格式是否允许"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    supported_extensions = {'pdf', 'png', 'jpg', 'jpeg'}
    return extension in supported_extensions

def process_files_with_mineru_api(file_paths, output_dir, app, is_ocr=True, enable_formula=True, enable_table=True, language="ch", layout_model="doclayout_yolo", saved_files=None):
    """使用MinerU API批量处理文件 - 严格按照test_input.py和test_output.py的逻辑"""
    try:
        # 检查文件格式
        valid_files = []
        supported_extensions = {'.pdf', '.png', '.jpg', '.jpeg'}
        
        for file_path in file_paths:
            path_obj = Path(file_path)
            if not path_obj.exists():
                print(f"⚠️ 文件不存在，跳过: {file_path}")
                continue
                
            if path_obj.suffix.lower() not in supported_extensions:
                print(f"⚠️ 不支持的文件格式，跳过: {file_path} (格式: {path_obj.suffix})")
                continue
                
            valid_files.append(str(file_path))
        
        if not valid_files:
            return {
                'success': False, 
                'error': '没有有效的文件可处理'
            }
        
        # 获取配置
        use_local = app.config.get('MINERU_USE_LOCAL', False)
        local_url = app.config.get('MINERU_LOCAL_URL', 'http://127.0.0.1:30000')
        
        # 创建MinerU客户端（支持API和本地调用）
        try:
            if use_local:
                api_client = MinerUAPI(use_local=True, local_url=local_url)
                print(f"🚀 MinerU 本地模式: {local_url}")
            else:
                token = app.config.get('MINERU_API_TOKEN')
                if not token:
                    return {
                        'success': False,
                        'error': 'MinerU API Token未配置，请在环境变量中设置MINERU_API_TOKEN，或设置MINERU_USE_LOCAL=true使用本地模式'
                    }
                api_client = MinerUAPI(token=token)
                print(f"🚀 MinerU API 模式")
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
        
        print(f"🚀 MinerU API 批量处理配置:")
        print(f"   📁 输入文件: {len(valid_files)} 个")
        print(f"   📁 输出目录: {output_dir}")
        print(f"   🔍 OCR: {is_ocr}")
        print(f"   📐 公式识别: {enable_formula}")
        print(f"   📊 表格识别: {enable_table}")
        print(f"   🌐 语言: {language}")
        print(f"   🏗️ 布局模型: {layout_model}")
        
        # 构建file_id映射和原始文件名映射（用于本地模式时传递正确的file_id和原始文件名）
        file_id_map = {}
        original_filename_map = {}
        if saved_files:
            for saved_file in saved_files:
                file_id = saved_file['file_id']
                saved_filename = saved_file['saved_filename']
                original_filename = saved_file['original_filename']
                # 查找对应的文件路径
                for file_path in valid_files:
                    if Path(file_path).name == saved_filename:
                        file_id_map[file_path] = file_id
                        original_filename_map[file_path] = original_filename
                        break
        
        # 批量处理文件
        result = api_client.process_files_batch(
            file_paths=valid_files,
            output_dir=str(output_dir),
            batch_index=0,
            max_files_per_batch=200,
            language=language,
            is_ocr=is_ocr,
            enable_formula=enable_formula,
            enable_table=enable_table,
            layout_model=layout_model,
            file_id_map=file_id_map if file_id_map else None,
            original_filename_map=original_filename_map if original_filename_map else None
        )
        
        if result['success']:
            print("✅ 批量处理成功")
            
            # 保存原始文件名信息到输出目录
            if saved_files:
                try:
                    output_path = Path(output_dir)
                    for saved_file in saved_files:
                        file_id = saved_file['file_id']
                        original_filename = saved_file['original_filename']
                        
                        # 查找对应的文件目录
                        for file_dir in output_path.iterdir():
                            if file_dir.is_dir() and file_id in file_dir.name:
                                # 创建原始文件名信息文件
                                filename_info = {
                                    'file_id': file_id,
                                    'original_filename': original_filename,
                                    'processed_at': time.time()
                                }
                                
                                filename_file = file_dir / 'filename_info.json'
                                with open(filename_file, 'w', encoding='utf-8') as f:
                                    json.dump(filename_info, f, ensure_ascii=False, indent=2)
                                
                                print(f"📝 保存原始文件名信息: {original_filename} -> {file_dir.name}")
                                break
                except Exception as e:
                    print(f"⚠️ 保存原始文件名信息失败: {str(e)}")
            
            return {'success': True, 'result': result}
        else:
            print(f"❌ 批量处理失败: {result['error']}")
            return {
                'success': False,
                'error': result['error']
            }
            
    except Exception as e:
        print(f"执行异常: {str(e)}")
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
    
    # 启用CORS，支持内网穿透
    CORS(app, 
         origins="*", 
         supports_credentials=True,
         allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    # 注册路由
    register_routes(app)
    
    return app

def _extract_library_id_from_path(file_dir):
    """从文件目录路径中提取文库ID"""
    try:
        path_parts = Path(file_dir).parts
        libraries_index = None
        for i, part in enumerate(path_parts):
            if part == 'libraries':
                libraries_index = i
                break
        
        if libraries_index is not None and libraries_index + 1 < len(path_parts):
            return path_parts[libraries_index + 1]
        return 'default'
    except Exception:
        return 'default'

def _find_file_directory(library_id, file_id, output_dir, search_all_libraries=False):
    """查找文件目录的辅助函数"""
    if search_all_libraries:
        libraries_dir = output_dir / 'libraries'
        if libraries_dir.exists():
            for lib_dir in libraries_dir.iterdir():
                if not lib_dir.is_dir():
                    continue
                file_dir = _find_file_in_library(lib_dir, file_id)
                if file_dir:
                    return file_dir, lib_dir.name
    else:
        library_dir = output_dir / 'libraries' / library_id
        if library_dir.exists():
            file_dir = _find_file_in_library(library_dir, file_id)
            if file_dir:
                return file_dir, library_id
    return None, None

def _find_file_in_library(library_dir, file_id):
    """在指定文库中查找文件目录"""
    potential_file_dir = library_dir / file_id
    if potential_file_dir.exists():
        # Check for subdirectory (e.g., {file_id}_b1)
        for sub_dir in potential_file_dir.iterdir():
            if sub_dir.is_dir() and sub_dir.name.endswith('_b1'):
                return sub_dir
        return potential_file_dir
    else:
        # Try to find directory containing file_id
        for sub_dir in library_dir.iterdir():
            if sub_dir.is_dir() and file_id in sub_dir.name:
                # Check for nested subdirectory
                for sub_sub_dir in sub_dir.iterdir():
                    if sub_sub_dir.is_dir() and sub_sub_dir.name.endswith('_b1'):
                        return sub_sub_dir
                return sub_dir
    return None

def _extract_filename_from_file_dir(file_dir):
    """从文件目录提取文件名"""
    filename_info_file = file_dir / 'filename_info.json'
    if filename_info_file.exists():
        try:
            with open(filename_info_file, 'r', encoding='utf-8') as f:
                filename_info = json.load(f)
                return filename_info.get('original_filename', '未命名文档')
        except Exception:
            pass
    
    # Fallback: try to extract from directory name
    dir_name = file_dir.name
    if '.pdf-' in dir_name:
        return dir_name.split('.pdf-')[0] + '.pdf'
    return '未命名文档'

def _process_image_paths(content, library_id, file_id):
    """处理markdown内容中的图片路径"""
    import re
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    
    def replace_image_path(match):
        alt_text = match.group(1)
        image_path = match.group(2)
        
        if not image_path.startswith(('http://', 'https://', '/')):
            if image_path.startswith('images/'):
                image_path = image_path[7:]
            api_path = f"/api/libraries/{library_id}/files/{file_id}/images/{image_path}"
            return f'![{alt_text}]({api_path})'
        return match.group(0)
    
    return re.sub(image_pattern, replace_image_path, content)

# 全局字典存储每个文档库的logger实例
_rag_loggers = {}

def _get_rag_logger(library_id):
    """获取或创建指定文档库的logger实例"""
    from loguru import logger
    from config import Config
    
    if library_id not in _rag_loggers:
        logs_dir = Config.LOGS_DIR
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件名格式: {library_id}_query.log
        log_file = logs_dir / f"{library_id}_query.log"
        
        # 创建独立的logger实例
        rag_logger = logger.bind(library_id=library_id)
        
        # 添加文件处理器，使用美观的格式，包含时间、级别、文档库ID和消息
        rag_logger.add(
            str(log_file),
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[library_id]}</cyan> | {message}",
            level="INFO",
            rotation="10 MB",
            retention="30 days",
            compression="zip",
            encoding="utf-8",
            enqueue=True,
            backtrace=True,
            diagnose=True
        )
        
        _rag_loggers[library_id] = rag_logger
    
    return _rag_loggers[library_id]

def _log_rag_query(library_id, question, answer, file_id=None, query_scope=None):
    """记录RAG查询日志到文件（使用Loguru，完整记录答案）"""
    try:
        from loguru import logger
        from config import Config
        
        # 获取或创建logger实例
        rag_logger = _get_rag_logger(library_id)
        
        # 构建完整的日志消息，答案不截断
        message_lines = [
            "📝 RAG Query",
            f"   📚 Library: {library_id}",
            f"   📄 File ID: {file_id or 'N/A'}",
            f"   🔍 Scope: {query_scope or 'N/A'}",
            f"   ❓ Question: {question}",
            "   💬 Answer:",
            answer  # 完整答案，不截断
        ]
        
        # 使用结构化格式记录，包含完整信息
        rag_logger.bind(
            library_id=library_id,
            file_id=file_id,
            query_scope=query_scope,
            question=question,
            answer=answer
        ).info("\n".join(message_lines))
            
    except ImportError:
        # 如果Loguru未安装，使用简单的文件写入
        try:
            from config import Config
            from datetime import datetime
            
            logs_dir = Config.LOGS_DIR
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / f"{library_id}_query.log"
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                'timestamp': timestamp,
                'level': 'INFO',
                'library_id': library_id,
                'file_id': file_id,
                'query_scope': query_scope,
                'question': question,
                'answer': answer
            }
            
            # 写入JSON格式，但格式化为更易读的形式
            log_line = f"{timestamp} | INFO     | {library_id} | "
            log_line += f"Library: {library_id}, File ID: {file_id or 'N/A'}, "
            log_line += f"Scope: {query_scope or 'N/A'}, Question: {question}, Answer: {answer}"
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except Exception as e:
            print(f"⚠️ 记录日志失败: {str(e)}")
    except Exception as e:
        # 日志记录失败不应该影响主流程
        print(f"⚠️ 记录日志失败: {str(e)}")

def _collect_files_from_library(library_dir, library_id):
    """从文库目录收集文件信息"""
    files = []
    for file_dir in library_dir.iterdir():
        if not file_dir.is_dir() or file_dir.name == 'info.json':
            continue
        
        # Find actual file directory (may be in subdirectory)
        actual_file_dir = file_dir
        filename_info_file = file_dir / 'filename_info.json'
        
        if not filename_info_file.exists():
            for sub_dir in file_dir.iterdir():
                if sub_dir.is_dir():
                    potential_info_file = sub_dir / 'filename_info.json'
                    if potential_info_file.exists():
                        actual_file_dir = sub_dir
                        filename_info_file = potential_info_file
                        break
        
        md_files = list(actual_file_dir.glob("*.md"))
        if md_files:
            md_file = md_files[0]
            filename = _extract_filename_from_file_dir(actual_file_dir)
            
            files.append({
                'id': file_dir.name,
                'library_id': library_id,
                'filename': filename,
                'created_at': md_file.stat().st_ctime
            })
    return files

# Global cache for RAG system instances to avoid repeated initialization
_rag_system_cache = {}
_rag_system_lock = None

def get_rag_system():
    """Get or create a cached RAG system instance"""
    global _rag_system_cache, _rag_system_lock
    
    if _rag_system_lock is None:
        import threading
        _rag_system_lock = threading.Lock()
    
    cache_key = "default"
    
    with _rag_system_lock:
        if cache_key not in _rag_system_cache:
            try:
                from RAG import PaperRAGSystem
                _rag_system_cache[cache_key] = PaperRAGSystem()
            except Exception as e:
                print(f"Failed to create RAG system: {str(e)}")
                raise
        
        return _rag_system_cache[cache_key]

def register_routes(app):
    """注册应用路由"""
    
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "*")
            response.headers.add('Access-Control-Allow-Methods', "*")
            return response
    
    @app.route('/api/upload', methods=['POST'])
    def upload_files():
        """处理文件上传 - 统一使用批量处理"""
        try:
            print(f"开始处理文件上传...")
            
            if 'files' not in request.files:
                return jsonify({'error': '没有文件'}), 400
            
            files = request.files.getlist('files')
            if not files or all(file.filename == '' for file in files):
                return jsonify({'error': '没有选择文件'}), 400
            
            print(f"上传 {len(files)} 个文件")
            
            # 获取用户选择的配置参数
            is_ocr = request.form.get('is_ocr', 'true').lower() == 'true'
            enable_formula = request.form.get('enable_formula', 'true').lower() == 'true'
            enable_table = request.form.get('enable_table', 'true').lower() == 'true'
            language = request.form.get('language', 'ch')
            layout_model = request.form.get('layout_model', 'doclayout_yolo')
            library_id = request.form.get('library_id', 'default')
            
            # 创建目录 - 放到指定文库下
            input_file_dir = app.config['INPUT_DIR']
            library_dir = app.config['OUTPUT_DIR'] / 'libraries' / library_id
            library_dir.mkdir(parents=True, exist_ok=True)
            
            # 确保文库有info.json文件
            info_file = library_dir / 'info.json'
            if not info_file.exists():
                if library_id == 'default':
                    library_info = {
                        'id': 'default',
                        'name': '默认文库',
                        'display_name': '默认文库',
                        'created_at': time.time(),
                        'description': '系统默认文库，用于存储未指定文库的文件'
                    }
                else:
                    # 对于其他文库，使用文库ID作为名称
                    library_info = {
                        'id': library_id,
                        'name': library_id.replace('_', ' ').replace('-', ' '),
                        'display_name': library_id.replace('_', ' ').replace('-', ' '),
                        'created_at': time.time(),
                        'description': ''
                    }
                
                with open(info_file, 'w', encoding='utf-8') as f:
                    json.dump(library_info, f, ensure_ascii=False, indent=2)
            
            # 保存文件并收集路径
            file_paths = []
            saved_files = []
            
            for file in files:
                if file.filename and allowed_file(file.filename, app):
                    # 生成文件ID
                    file_id = str(uuid.uuid4())
                    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
                    new_filename = f"{file_id}.{file_extension}" if file_extension else file_id
                    file_path = input_file_dir / new_filename
                    input_file_dir.mkdir(parents=True, exist_ok=True)
                    file.save(str(file_path))
                    
                    file_paths.append(str(file_path))
                    saved_files.append({
                        'file_id': file_id,
                        'original_filename': file.filename,
                        'saved_filename': new_filename
                    })
                else:
                    print(f"跳过不支持的文件: {file.filename}")
            
            if not file_paths:
                return jsonify({'error': '没有有效的文件'}), 400
            
            # 批量处理文件，直接输出到文库目录下
            try:
                print("开始调用MinerU API批量处理...")
                print(f"配置参数: OCR={is_ocr}, 公式={enable_formula}, 表格={enable_table}, 语言={language}, 模型={layout_model}")
                
                # 直接使用文库目录作为输出目录（本地模式会为每个文件创建对应的子目录）
                result = process_files_with_mineru_api(
                    file_paths, 
                    str(library_dir),  # 直接输出到文库目录
                    app, 
                    is_ocr=is_ocr, 
                    enable_formula=enable_formula, 
                    enable_table=enable_table,
                    language=language,
                    layout_model=layout_model,
                    saved_files=saved_files
                )
                
                if result['success']:
                    print("批量处理成功")
                    
                    # 处理结果已经在最终目录了，只需要整理返回信息
                    processed_files = []
                    success_count = 0
                    
                    for processed_file in result['result']['processed_files']:
                        if processed_file['success']:
                            # 从output_dir中提取目录名（格式：{文件名}-{file_id}）
                            output_dir_path = processed_file.get('output_dir', '')
                            if output_dir_path:
                                # 从路径中提取目录名
                                dir_name = Path(output_dir_path).name
                                # 从目录名中提取file_id（最后一个-后面的部分）
                                if '-' in dir_name:
                                    file_id = dir_name.rsplit('-', 1)[-1]
                                else:
                                    # 如果没有-，说明可能格式不对，尝试从data_id获取
                                    data_id = processed_file.get('data_id', '')
                                    file_id = data_id.replace('_b1', '') if data_id else ''
                                
                                processed_files.append({
                                    'file_id': file_id,
                                    'original_filename': processed_file.get('original_name', ''),
                                    'success': True
                                })
                                success_count += 1
                                print(f"✅ 文件处理成功: {processed_file.get('original_name', '')} -> {output_dir_path}")
                            else:
                                processed_files.append({
                                    'file_id': '',
                                    'original_filename': processed_file.get('original_name', ''),
                                    'success': False,
                                    'error': '缺少data_id'
                                })
                        else:
                            processed_files.append({
                                'file_id': '',
                                'original_filename': processed_file.get('original_name', ''),
                                'success': False,
                                'error': processed_file.get('error', '处理失败')
                            })
                    
                    return jsonify({
                        'success': True,
                        'processed_files': processed_files,
                        'success_count': success_count,
                        'total_count': len(file_paths),
                        'message': f'批量处理完成，成功: {success_count}/{len(file_paths)}'
                    })
                else:
                    print(f"批量处理失败: {result['error']}")
                    return jsonify({'error': result['error']}), 500
            except Exception as e:
                print(f"批量处理异常: {str(e)}")
                traceback.print_exc()
                return jsonify({'error': f'批量处理失败: {str(e)}'}), 500
                
        except Exception as e:
            print(f"上传处理异常: {str(e)}")
            traceback.print_exc()
            return jsonify({'error': f'上传失败: {str(e)}'}), 500


    @app.route('/api/files', methods=['GET'])
    def get_files():
        """获取已处理的文件列表，支持按文库ID过滤"""
        try:
            library_id = request.args.get('library_id', 'default')
            files = []
            libraries_dir = app.config['OUTPUT_DIR'] / 'libraries'
            
            if libraries_dir.exists():
                if library_id != 'all':
                    library_dir = libraries_dir / library_id
                    if library_dir.exists() and library_dir.is_dir():
                        files = _collect_files_from_library(library_dir, library_id)
                else:
                    for lib_dir in libraries_dir.iterdir():
                        if lib_dir.is_dir():
                            files.extend(_collect_files_from_library(lib_dir, lib_dir.name))
            
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return jsonify({'files': files})
            
        except Exception as e:
            return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>/content', methods=['GET'])
    def get_library_file_content(library_id, file_id):
        """获取指定文库中指定文件的markdown内容"""
        try:
            file_dir, _ = _find_file_directory(library_id, file_id, app.config['OUTPUT_DIR'])
            
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            md_files = list(file_dir.glob("*.md"))
            if not md_files:
                return jsonify({'error': '未找到markdown文件'}), 404
            
            with open(md_files[0], 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = _process_image_paths(content, library_id, file_id)
            
            return jsonify({
                'content': content,
                'file_id': file_id,
                'library_id': library_id
            })
            
        except Exception as e:
            print(f"获取文件内容失败: {str(e)}")
            return jsonify({'error': f'获取文件内容失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>/content', methods=['GET'])
    def get_file_content(file_id):
        """获取指定文件的markdown内容"""
        try:
            file_dir, library_id = _find_file_directory(None, file_id, app.config['OUTPUT_DIR'], search_all_libraries=True)
            
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            md_files = list(file_dir.glob("*.md"))
            if not md_files:
                return jsonify({'error': '未找到markdown文件'}), 404
            
            md_file = md_files[0]
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            content = _process_image_paths(content, library_id, file_id)
            filename = md_file.stem.replace('_', ' ').replace('-', ' ')
            
            return jsonify({
                'content': content,
                'filename': filename,
                'file_id': file_id,
                'library_id': library_id
            })
            
        except Exception as e:
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>/images/<path:image_path>')
    def get_library_image(library_id, file_id, image_path):
        """获取指定文库中指定文件的图片"""
        try:
            file_dir, found_library_id = _find_file_directory(library_id, file_id, app.config['OUTPUT_DIR'])
            
            if not file_dir:
                print(f"❌ 图片404: 文件目录不存在 - library_id={library_id}, file_id={file_id}")
                return jsonify({'error': '文件目录不存在'}), 404
            
            image_file = file_dir / "images" / image_path
            if not image_file.exists():
                # 尝试查找所有可能的图片文件
                images_dir = file_dir / "images"
                if images_dir.exists():
                    available_images = list(images_dir.glob("*"))
                    print(f"❌ 图片404: 图片不存在 - 请求路径: {image_path}")
                    print(f"   文件目录: {file_dir}")
                    print(f"   图片目录: {images_dir}")
                    print(f"   可用图片文件: {[img.name for img in available_images[:5]]}")
                else:
                    print(f"❌ 图片404: 图片目录不存在 - {images_dir}")
                return jsonify({'error': '图片不存在'}), 404
            
            response = send_from_directory(str(image_file.parent), image_path)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Cache-Control'] = 'public, max-age=31536000'
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            response.headers['ETag'] = f'"{image_path}_{image_file.stat().st_mtime}"'
            
            return response
            
        except Exception as e:
            print(f"❌ 获取文库图片失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'获取图片失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>/images/<path:image_path>')
    def get_image(file_id, image_path):
        """获取图片文件"""
        try:
            file_dir, _ = _find_file_directory(None, file_id, app.config['OUTPUT_DIR'], search_all_libraries=True)
            
            if not file_dir:
                return jsonify({'error': '文件目录不存在'}), 404
            
            image_file = file_dir / "images" / image_path
            if not image_file.exists():
                return jsonify({'error': '图片不存在'}), 404
            
            response = send_from_directory(str(image_file.parent), image_path)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            response.headers['Cache-Control'] = 'public, max-age=31536000'
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            response.headers['ETag'] = f'"{image_path}_{image_file.stat().st_mtime}"'
            
            return response
            
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
            'is_ocr': True,
            'enable_formula': False,
            'defaults': {
                'is_ocr': True,
                'enable_formula': False
            }
        })

    @app.route('/api/libraries', methods=['GET'])
    def get_libraries():
        """获取用户文库列表"""
        try:
            libraries = []
            libraries_dir = app.config['OUTPUT_DIR'] / 'libraries'
            
            # 确保默认文库存在
            default_library_dir = libraries_dir / 'default'
            if not default_library_dir.exists():
                default_library_dir.mkdir(parents=True, exist_ok=True)
                # 创建默认文库信息文件
                default_info = {
                    'id': 'default',
                    'name': '默认文库',
                    'display_name': '默认文库',
                    'description': '系统默认文库',
                    'created_at': datetime.now().isoformat()
                }
                with open(default_library_dir / 'info.json', 'w', encoding='utf-8') as f:
                    json.dump(default_info, f, ensure_ascii=False, indent=2)
            
            if libraries_dir.exists():
                for library_dir in libraries_dir.iterdir():
                    if library_dir.is_dir():
                        # 读取文库信息
                        library_info = {
                            'id': library_dir.name,
                            'name': library_dir.name.replace('_', ' ').title(),
                            'display_name': library_dir.name.replace('_', ' ').title(),
                            'created_at': library_dir.stat().st_ctime,
                            'file_count': 0
                        }
                        
                        # 尝试读取info.json文件获取真实的中文名称
                        info_file = library_dir / 'info.json'
                        if info_file.exists():
                            try:
                                with open(info_file, 'r', encoding='utf-8') as f:
                                    saved_info = json.load(f)
                                    library_info['name'] = saved_info.get('name', library_info['name'])
                                    library_info['display_name'] = saved_info.get('display_name', library_info['name'])
                            except:
                                pass
                        
                        # 统计文件数量
                        file_count = 0
                        for file_dir in library_dir.iterdir():
                            if file_dir.is_dir():
                                metadata_file = file_dir / 'metadata.json'
                                if metadata_file.exists():
                                    file_count += 1
                        
                        library_info['file_count'] = file_count
                        libraries.append(library_info)
            
            # 按创建时间排序
            libraries.sort(key=lambda x: x['created_at'], reverse=True)
            print(f"找到 {len(libraries)} 个文库:")
            for lib in libraries:
                print(f"  - {lib['id']}: {lib['name']}")
            return jsonify({'data': libraries})
            
        except Exception as e:
            return jsonify({'error': f'获取文库列表失败: {str(e)}'}), 500

    @app.route('/api/libraries', methods=['POST'])
    def create_library():
        """创建新文库"""
        try:
            data = request.get_json()
            library_name = data.get('name', '').strip()
            
            if not library_name:
                return jsonify({'error': '文库名称不能为空'}), 400
            
            # 生成文库ID - 只使用英文字母、数字和下划线
            library_id = library_name.lower().replace(' ', '_').replace('-', '_')
            library_id = ''.join(c for c in library_id if c.isalnum() or c == '_')
            # 如果包含中文字符，生成一个随机的英文ID
            if not library_id or any('\u4e00' <= c <= '\u9fff' for c in library_name):
                import uuid
                library_id = f"library_{uuid.uuid4().hex[:8]}"
            
            # 创建文库目录
            library_dir = app.config['OUTPUT_DIR'] / 'libraries' / library_id
            library_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存文库信息
            library_info = {
                'id': library_id,
                'name': library_name,  # 保存用户输入的中文名称用于显示
                'display_name': library_name,  # 显示名称
                'created_at': time.time(),
                'description': data.get('description', '')
            }
            
            info_file = library_dir / 'info.json'
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(library_info, f, ensure_ascii=False, indent=2)
            
            return jsonify({
                'success': True,
                'library': library_info,
                'message': '文库创建成功'
            })
            
        except Exception as e:
            return jsonify({'error': f'创建文库失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files', methods=['GET'])
    def get_library_files(library_id):
        """获取文库中的文件列表"""
        try:
            library_dir = app.config['OUTPUT_DIR'] / 'libraries' / library_id
            
            if not library_dir.exists():
                return jsonify({'data': []})
            
            files = []
            for file_dir in library_dir.iterdir():
                if not file_dir.is_dir() or file_dir.name == 'info.json':
                    continue
                
                # Find actual file directory
                actual_file_dir = file_dir
                filename_info_file = file_dir / 'filename_info.json'
                
                if not filename_info_file.exists():
                    for sub_dir in file_dir.iterdir():
                        if sub_dir.is_dir():
                            potential_info_file = sub_dir / 'filename_info.json'
                            if potential_info_file.exists():
                                actual_file_dir = sub_dir
                                filename_info_file = potential_info_file
                                break
                
                if filename_info_file.exists():
                    try:
                        with open(filename_info_file, 'r', encoding='utf-8') as f:
                            file_info = json.load(f)
                        files.append({
                            'id': file_dir.name,
                            'name': file_info.get('original_filename', file_dir.name),
                            'created_at': file_info.get('upload_time', datetime.now().isoformat()),
                            'size': file_info.get('file_size', 0),
                            'status': file_info.get('status', 'processed'),
                            'is_ocr': file_info.get('is_ocr', True),
                            'enable_formula': file_info.get('enable_formula', False)
                        })
                    except Exception:
                        continue
                else:
                    # Fallback logic
                    original_filename = _extract_filename_from_file_dir(file_dir)
                    full_md_file = actual_file_dir / 'full.md'
                    status = 'processed' if full_md_file.exists() else 'processing'
                    
                    file_size = 0
                    for file in actual_file_dir.iterdir():
                        if file.is_file() and file.name.endswith('_origin.pdf'):
                            file_size = file.stat().st_size
                            break
                    
                    files.append({
                        'id': file_dir.name,
                        'name': original_filename,
                        'created_at': datetime.now().isoformat(),
                        'size': file_size,
                        'status': status,
                        'is_ocr': True,
                        'enable_formula': False
                    })
            
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return jsonify({'data': files})
            
        except Exception as e:
            print(f"获取文库文件失败: {str(e)}")
            return jsonify({'error': f'获取文库文件失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>', methods=['DELETE'])
    def delete_library_file(library_id, file_id):
        """删除文库中的文件"""
        try:
            library_dir = app.config['OUTPUT_DIR'] / 'libraries' / library_id
            
            if not library_dir.exists():
                return jsonify({'error': '文库不存在'}), 404
            
            file_dir = _find_file_in_library(library_dir, file_id)
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            shutil.rmtree(file_dir)
            
            # 如果文库为空且不是默认文库，删除文库目录
            if library_dir.exists() and not any(library_dir.iterdir()) and library_dir.name != 'default':
                shutil.rmtree(library_dir)
            
            return jsonify({'message': '文件删除成功'})
            
        except Exception as e:
            print(f"删除文件失败: {str(e)}")
            return jsonify({'error': f'删除文件失败: {str(e)}'}), 500





    @app.route('/api/libraries/<library_id>/files/<file_id>/process', methods=['POST'])
    def process_library_file(library_id, file_id):
        """处理文库中的文件"""
        try:
            library_dir = app.config['OUTPUT_DIR'] / 'libraries' / library_id
            file_dir = library_dir / file_id
            
            if not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            # 读取元数据
            metadata_file = file_dir / 'metadata.json'
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 查找原始文件
            original_filename = metadata['original_filename']
            file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            input_file_path = app.config['INPUT_DIR'] / f"{file_id}.{file_extension}"
            
            if not input_file_path.exists():
                return jsonify({'error': '原始文件不存在'}), 404
            
            # 更新状态
            metadata['status'] = 'processing'
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 调用MinerU API处理文件
            try:
                result = process_files_with_mineru_api(
                    [str(input_file_path)], 
                    str(file_dir), 
                    app, 
                    metadata.get('is_ocr', True), 
                    metadata.get('enable_formula', False)
                )
                
                if result['success']:
                    metadata['status'] = 'completed'
                    metadata['processed_time'] = time.time()
                else:
                    metadata['status'] = 'failed'
                    metadata['error'] = result['error']
                
                # 更新元数据
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                return jsonify({
                    'success': result['success'],
                    'message': '文件处理完成' if result['success'] else f'文件处理失败: {result["error"]}'
                })
                
            except Exception as e:
                metadata['status'] = 'failed'
                metadata['error'] = str(e)
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                return jsonify({'error': f'文件处理失败: {str(e)}'}), 500
            
        except Exception as e:
            return jsonify({'error': f'处理文件失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>/rag', methods=['POST'])
    def query_paper_rag(library_id, file_id):
        """单篇论文RAG查询"""
        try:
            data = request.get_json()
            question = data.get('question', '')
            query_mode = data.get('query_mode', 'single_paper')
            
            if not question:
                return jsonify({'error': '问题不能为空'}), 400
            
            # Get cached RAG system instance
            try:
                rag_system = get_rag_system()
            except ImportError:
                return jsonify({'error': 'RAG系统未找到，请确保agent/RAG.py存在'}), 500
            except Exception as e:
                return jsonify({'error': f'RAG系统初始化失败: {str(e)}'}), 500
            
            # 尝试加载向量数据库
            if not rag_system.load_vector_store(library_id=library_id):
                return jsonify({
                    'error': f'向量数据库不存在，请先为文库 {library_id} 构建向量数据库',
                    'hint': '可以在问答页面点击"立即构建"按钮来构建向量数据库'
                }), 404
            
            # 根据查询模式选择查询方式
            if query_mode == 'single_paper':
                # 查询单篇论文
                result = rag_system.query_with_sources(question, k=4, file_id=file_id)
            else:
                # 查询整个数据库
                result = rag_system.query_with_sources(question, k=4, file_id=None)
            
            # 记录日志
            answer = result.get('answer', '')
            query_scope = result.get('query_scope', query_mode)
            _log_rag_query(library_id, question, answer, file_id=file_id, query_scope=query_scope)
            
            return jsonify({
                'success': True,
                'answer': answer,
                'sources': result.get('sources', []),
                'paper_count': result.get('paper_count', 0),
                'query_scope': query_scope
            })
            
        except Exception as e:
            print(f"RAG查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'RAG查询失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/rag', methods=['POST'])
    def query_library_rag(library_id):
        """整个文档库RAG查询"""
        try:
            data = request.get_json()
            question = data.get('question', '')
            
            if not question:
                return jsonify({'error': '问题不能为空'}), 400
            
            # Get cached RAG system instance
            try:
                rag_system = get_rag_system()
            except ImportError:
                return jsonify({'error': 'RAG系统未找到，请确保agent/RAG.py存在'}), 500
            except Exception as e:
                return jsonify({'error': f'RAG系统初始化失败: {str(e)}'}), 500
            
            # 尝试加载向量数据库
            if not rag_system.load_vector_store(library_id=library_id):
                return jsonify({
                    'error': f'向量数据库不存在，请先为文库 {library_id} 构建向量数据库',
                    'hint': '可以在问答页面点击"立即构建"按钮来构建向量数据库'
                }), 404
            
            # 查询整个文档库
            result = rag_system.query_with_sources(question, k=4, file_id=None)
            
            # 记录日志
            answer = result.get('answer', '')
            _log_rag_query(library_id, question, answer, file_id=None, query_scope='all_papers')
            
            return jsonify({
                'success': True,
                'answer': answer,
                'sources': result.get('sources', []),
                'paper_count': result.get('paper_count', 0),
                'query_scope': result.get('query_scope', 'all_papers')
            })
            
        except Exception as e:
            print(f"RAG查询失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'RAG查询失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/build_vector_store', methods=['POST'])
    def build_library_vector_store(library_id):
        """构建文库的向量数据库"""
        try:
            # Get cached RAG system instance
            try:
                rag_system = get_rag_system()
            except ImportError:
                return jsonify({'error': 'RAG系统未找到，请确保agent/RAG.py存在'}), 500
            except Exception as e:
                return jsonify({'error': f'RAG系统初始化失败: {str(e)}'}), 500
            
            # 加载论文
            papers = rag_system.load_papers_from_library(library_id=library_id)
            
            if not papers:
                return jsonify({
                    'success': False,
                    'error': f'文库 {library_id} 中没有找到论文，请先上传论文'
                }), 404
            
            # 构建向量数据库
            success = rag_system.build_vector_store(papers, library_id=library_id)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'向量数据库构建成功，共处理 {len(papers)} 篇论文',
                    'paper_count': len(papers)
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '向量数据库构建失败，请查看日志'
                }), 500
            
        except Exception as e:
            print(f"构建向量数据库失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'构建向量数据库失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/vector_store_status', methods=['GET'])
    def get_vector_store_status(library_id):
        """获取向量数据库状态"""
        try:
            # Get cached RAG system instance
            try:
                rag_system = get_rag_system()
            except ImportError:
                return jsonify({'error': 'RAG系统未找到'}), 500
            except Exception as e:
                return jsonify({'error': f'RAG系统初始化失败: {str(e)}'}), 500
            
            # Check if vector store exists without actually loading it
            # This prevents overwriting the current vector store in shared instance
            exists, paper_count = rag_system.check_vector_store_exists(library_id=library_id)
            
            return jsonify({
                'exists': exists,
                'paper_count': paper_count
            })
            
        except Exception as e:
            print(f"检查向量数据库状态失败: {str(e)}")
            return jsonify({
                'exists': False,
                'error': str(e)
            }), 500



# 创建应用实例
app = create_app(os.environ.get('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # 获取本机IP地址，支持外部访问
    import socket
    def get_local_ip():
        try:
            # 创建一个socket连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    host = get_local_ip()
    port = 5000
    
    print(f"🌐 后端服务启动信息:")
    print(f"   本地访问: http://127.0.0.1:{port}")
    print(f"   网络访问: http://{host}:{port}")
    print(f"   API文档: http://{host}:{port}/api/docs")
    
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=port)