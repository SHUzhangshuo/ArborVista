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
        
        # 获取API Token
        token = app.config.get('MINERU_API_TOKEN')
        if not token:
            return {
                'success': False,
                'error': 'MinerU API Token未配置，请在环境变量中设置MINERU_API_TOKEN'
            }
        
        # 创建MinerU API客户端
        api_client = MinerUAPI(token)
        
        print(f"🚀 MinerU API 批量处理配置:")
        print(f"   📁 输入文件: {len(valid_files)} 个")
        print(f"   📁 输出目录: {output_dir}")
        print(f"   🔍 OCR: {is_ocr}")
        print(f"   📐 公式识别: {enable_formula}")
        print(f"   📊 表格识别: {enable_table}")
        print(f"   🌐 语言: {language}")
        print(f"   🏗️ 布局模型: {layout_model}")
        
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
            layout_model=layout_model
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
        # 文件路径格式: output/libraries/{library_id}/{file_id}
        path_parts = Path(file_dir).parts
        libraries_index = None
        for i, part in enumerate(path_parts):
            if part == 'libraries':
                libraries_index = i
                break
        
        if libraries_index is not None and libraries_index + 1 < len(path_parts):
            return path_parts[libraries_index + 1]
        else:
            return 'default'  # 如果无法提取，返回默认文库
    except Exception:
        return 'default'

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
            method = request.form.get('method', 'auto')
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
            
            # 批量处理文件，但将结果直接存储到文库目录下
            try:
                print("开始调用MinerU API批量处理...")
                print(f"配置参数: OCR={is_ocr}, 公式={enable_formula}, 表格={enable_table}, 语言={language}, 模型={layout_model}")
                
                # 创建一个临时批次目录用于MinerU API处理
                batch_id = str(uuid.uuid4())
                temp_batch_dir = library_dir / batch_id
                temp_batch_dir.mkdir(exist_ok=True)
                
                result = process_files_with_mineru_api(
                    file_paths, 
                    str(temp_batch_dir), 
                    app, 
                    is_ocr=is_ocr, 
                    enable_formula=enable_formula, 
                    enable_table=enable_table,
                    language=language,
                    layout_model=layout_model,
                    saved_files=saved_files
                )
                
                if result['success']:
                    print("批量处理成功，开始重新组织文件结构...")
                    
                    # 将处理结果从临时批次目录移动到文库目录下
                    processed_files = []
                    success_count = 0
                    
                    for processed_file in result['result']['processed_files']:
                        if processed_file['success']:
                            # 查找处理后的文件目录
                            data_id = processed_file.get('data_id', '')
                            if data_id:
                                source_dir = temp_batch_dir / data_id
                                if source_dir.exists():
                                    # 创建目标文件目录
                                    file_id = data_id.replace('_b1', '')  # 移除_b1后缀
                                    target_dir = library_dir / file_id
                                    
                                    # 移动文件
                                    if target_dir.exists():
                                        shutil.rmtree(target_dir)
                                    shutil.move(str(source_dir), str(target_dir))
                                    
                                    processed_files.append({
                                        'file_id': file_id,
                                        'original_filename': processed_file.get('original_name', ''),
                                        'success': True
                                    })
                                    success_count += 1
                                    print(f"✅ 文件移动成功: {processed_file.get('original_name', '')} -> {target_dir}")
                                else:
                                    processed_files.append({
                                        'file_id': data_id,
                                        'original_filename': processed_file.get('original_name', ''),
                                        'success': False,
                                        'error': '处理后的文件目录不存在'
                                    })
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
                    
                    # 清理临时批次目录
                    if temp_batch_dir.exists():
                        shutil.rmtree(temp_batch_dir)
                    
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
                # 如果指定了文库ID，只遍历该文库
                if library_id != 'all':
                    library_dir = libraries_dir / library_id
                    if library_dir.exists() and library_dir.is_dir():
                        # 直接遍历文库内的文件目录（不再通过批次目录）
                        for file_dir in library_dir.iterdir():
                            if file_dir.is_dir() and file_dir.name != 'info.json':
                                # 查找markdown文件
                                md_files = list(file_dir.glob("*.md"))
                                if md_files:
                                    md_file = md_files[0]
                                    
                                    # 尝试从filename_info.json文件获取原始文件名
                                    filename = "未命名文档"  # 默认文件名
                                    
                                    # 查找filename_info.json文件
                                    filename_info_file = file_dir / 'filename_info.json'
                                    if filename_info_file.exists():
                                        try:
                                            with open(filename_info_file, 'r', encoding='utf-8') as f:
                                                filename_info = json.load(f)
                                                filename = filename_info.get('original_filename', '未命名文档')
                                        except Exception as e:
                                            print(f"读取filename_info.json失败: {str(e)}")
                                    else:
                                        # 如果没有filename_info.json，尝试从origin文件获取
                                        origin_files = list(file_dir.glob("*_origin.*"))
                                        if origin_files:
                                            origin_file = origin_files[0]
                                            # 从origin文件名中提取原始名称
                                            origin_name = origin_file.stem
                                            if '_origin' in origin_name:
                                                # 移除_origin后缀
                                                original_name = origin_name.replace('_origin', '')
                                                # 移除file_id部分，保留原始文件名
                                                if '_' in original_name:
                                                    parts = original_name.split('_')
                                                    if len(parts) > 1:
                                                        # 重新组合除了第一部分（file_id）之外的所有部分
                                                        filename = '_'.join(parts[1:])
                                                    else:
                                                        filename = original_name
                                                else:
                                                    filename = original_name
                                    
                                    files.append({
                                        'id': file_dir.name,
                                        'library_id': library_id,
                                        'filename': filename,
                                        'created_at': md_file.stat().st_ctime
                                    })
                else:
                    # 遍历所有文库目录
                    for library_dir in libraries_dir.iterdir():
                        if library_dir.is_dir():
                            # 直接遍历文库内的文件目录（不再通过批次目录）
                            for file_dir in library_dir.iterdir():
                                if file_dir.is_dir() and file_dir.name != 'info.json':
                                    # 查找markdown文件
                                    md_files = list(file_dir.glob("*.md"))
                                    if md_files:
                                        md_file = md_files[0]
                                        
                                        # 尝试从filename_info.json文件获取原始文件名
                                        filename = "未命名文档"  # 默认文件名
                                        
                                        # 查找filename_info.json文件
                                        filename_info_file = file_dir / 'filename_info.json'
                                        if filename_info_file.exists():
                                            try:
                                                with open(filename_info_file, 'r', encoding='utf-8') as f:
                                                    filename_info = json.load(f)
                                                    filename = filename_info.get('original_filename', '未命名文档')
                                            except Exception as e:
                                                print(f"读取filename_info.json失败: {str(e)}")
                                        else:
                                            # 如果没有filename_info.json，尝试从origin文件获取
                                            origin_files = list(file_dir.glob("*_origin.*"))
                                            if origin_files:
                                                origin_file = origin_files[0]
                                                # 从origin文件名中提取原始名称
                                                origin_name = origin_file.stem
                                                if '_origin' in origin_name:
                                                    # 移除_origin后缀
                                                    original_name = origin_name.replace('_origin', '')
                                                    # 移除file_id部分，保留原始文件名
                                                    if '_' in original_name:
                                                        parts = original_name.split('_')
                                                        if len(parts) > 1:
                                                            # 重新组合除了第一部分（file_id）之外的所有部分
                                                            filename = '_'.join(parts[1:])
                                                        else:
                                                            filename = original_name
                                                    else:
                                                        filename = original_name
                                        
                                        files.append({
                                            'id': file_dir.name,
                                            'library_id': library_dir.name,
                                            'filename': filename,
                                            'created_at': md_file.stat().st_ctime
                                        })
            
            # 按创建时间排序
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return jsonify({'files': files})
            
        except Exception as e:
            return jsonify({'error': f'获取文件列表失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>/content', methods=['GET'])
    def get_library_file_content(library_id, file_id):
        """获取指定文库中指定文件的markdown内容"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            
            # 查找文件目录（直接在指定文库下）
            file_dir = None
            
            libraries_dir = output_dir / 'libraries' / library_id
            if libraries_dir.exists():
                # 直接查找文件目录
                potential_file_dir = libraries_dir / file_id
                if potential_file_dir.exists():
                    file_dir = potential_file_dir
                    # 检查是否有子目录（如 {file_id}_b1）
                    for sub_dir in potential_file_dir.iterdir():
                        if sub_dir.is_dir() and sub_dir.name.endswith('_b1'):
                            file_dir = sub_dir
                            break
                else:
                    # 如果直接匹配失败，尝试查找包含file_id的目录（处理_b1后缀等情况）
                    for sub_dir in libraries_dir.iterdir():
                        if sub_dir.is_dir() and file_id in sub_dir.name:
                            file_dir = sub_dir
                            # 检查是否有子目录（如 {file_id}_b1）
                            for sub_sub_dir in sub_dir.iterdir():
                                if sub_sub_dir.is_dir() and sub_sub_dir.name.endswith('_b1'):
                                    file_dir = sub_sub_dir
                                    break
                            break
            
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            # 查找markdown文件
            md_files = list(file_dir.glob("*.md"))
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
                
                # 如果是相对路径的图片，转换为API路径
                if not image_path.startswith('http') and not image_path.startswith('/'):
                    # 如果路径已经包含images/前缀，去掉它
                    if image_path.startswith('images/'):
                        image_path = image_path[7:]  # 去掉 "images/" 前缀
                    
                    # 构建图片API路径 - 使用文库图片API接口
                    # 需要从文件路径中提取library_id
                    library_id = _extract_library_id_from_path(file_dir)
                    api_path = f"/api/libraries/{library_id}/files/{file_id}/images/{image_path}"
                    return f'![{alt_text}]({api_path})'
                return match.group(0)
            
            # 替换所有图片路径
            content = re.sub(image_pattern, replace_image_path, content)
            
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
            output_dir = app.config['OUTPUT_DIR']
            
            # 查找文件目录（直接在文库下）
            file_dir = None
            library_id = None
            
            libraries_dir = output_dir / 'libraries'
            if libraries_dir.exists():
                for library_dir in libraries_dir.iterdir():
                    if library_dir.is_dir():
                        # 直接查找文件目录
                        potential_file_dir = library_dir / file_id
                        if potential_file_dir.exists():
                            file_dir = potential_file_dir
                            library_id = library_dir.name
                            # 检查是否有子目录（如 {file_id}_b1）
                            for sub_dir in potential_file_dir.iterdir():
                                if sub_dir.is_dir() and sub_dir.name.endswith('_b1'):
                                    file_dir = sub_dir
                                    break
                            break
                        else:
                            # 如果直接匹配失败，尝试查找包含file_id的目录（处理_b1后缀等情况）
                            for sub_dir in library_dir.iterdir():
                                if sub_dir.is_dir() and file_id in sub_dir.name:
                                    file_dir = sub_dir
                                    library_id = library_dir.name
                                    # 检查是否有子目录（如 {file_id}_b1）
                                    for sub_sub_dir in sub_dir.iterdir():
                                        if sub_sub_dir.is_dir() and sub_sub_dir.name.endswith('_b1'):
                                            file_dir = sub_sub_dir
                                            break
                                    break
                            if file_dir:
                                break
            
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            # 查找markdown文件
            md_files = list(file_dir.glob("*.md"))
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
                    # 如果路径已经包含images目录，直接使用文件名
                    if image_path.startswith('images/'):
                        filename = image_path.replace('images/', '')
                        # 使用文库图片API接口
                        library_id = _extract_library_id_from_path(file_dir)
                        api_path = f"/api/libraries/{library_id}/files/{file_id}/images/{filename}"
                        print(f"路径已包含images目录，转换为API路径: {api_path}")
                        return f'![{alt_text}]({api_path})'
                    else:
                        # 构建API路径
                        library_id = _extract_library_id_from_path(file_dir)
                        api_path = f"/api/libraries/{library_id}/files/{file_id}/images/{image_path}"
                        print(f"转换为API路径: {api_path}")
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
                'file_id': file_id,
                'library_id': library_id
            })
            
        except Exception as e:
            return jsonify({'error': f'读取文件失败: {str(e)}'}), 500

    @app.route('/api/libraries/<library_id>/files/<file_id>/images/<path:image_path>')
    def get_library_image(library_id, file_id, image_path):
        """获取指定文库中指定文件的图片"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            
            # 查找文件目录（直接在指定文库下）
            file_dir = None
            libraries_dir = output_dir / 'libraries' / library_id
            if libraries_dir.exists():
                # 直接查找文件目录
                potential_file_dir = libraries_dir / file_id
                if potential_file_dir.exists():
                    file_dir = potential_file_dir
                    # 检查是否有子目录（如 {file_id}_b1）
                    for sub_dir in potential_file_dir.iterdir():
                        if sub_dir.is_dir() and sub_dir.name.endswith('_b1'):
                            file_dir = sub_dir
                            break
                else:
                    # 如果直接匹配失败，尝试查找包含file_id的目录（处理_b1后缀等情况）
                    for sub_dir in libraries_dir.iterdir():
                        if sub_dir.is_dir() and file_id in sub_dir.name:
                            file_dir = sub_dir
                            # 检查是否有子目录（如 {file_id}_b1）
                            for sub_sub_dir in sub_dir.iterdir():
                                if sub_sub_dir.is_dir() and sub_sub_dir.name.endswith('_b1'):
                                    file_dir = sub_sub_dir
                                    break
                            break
            
            if not file_dir:
                return jsonify({'error': '文件目录不存在'}), 404
            
            # 图片文件在 file_id/images 子目录中
            image_file = file_dir / "images" / image_path
            
            if not image_file.exists():
                return jsonify({'error': '图片不存在'}), 404
            # 添加 CORS 头部支持和缓存头
            response = send_from_directory(str(image_file.parent), image_path)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            # 设置缓存头，让浏览器缓存图片1年
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1年
            response.headers['Expires'] = 'Thu, 31 Dec 2025 23:59:59 GMT'
            response.headers['ETag'] = f'"{image_path}_{image_file.stat().st_mtime}"'
            
            return response
            
        except Exception as e:
            print(f"获取文库图片失败: {str(e)}")
            return jsonify({'error': f'获取图片失败: {str(e)}'}), 500

    @app.route('/api/files/<file_id>/images/<path:image_path>')
    def get_image(file_id, image_path):
        """获取图片文件"""
        try:
            output_dir = app.config['OUTPUT_DIR']
            
            # 查找文件目录（在所有文库中）
            file_dir = None
            libraries_dir = output_dir / 'libraries'
            if libraries_dir.exists():
                for library_dir in libraries_dir.iterdir():
                    if library_dir.is_dir():
                        # 直接查找文件目录
                        potential_file_dir = library_dir / file_id
                        if potential_file_dir.exists():
                            file_dir = potential_file_dir
                            # 检查是否有子目录（如 {file_id}_b1）
                            for sub_dir in potential_file_dir.iterdir():
                                if sub_dir.is_dir() and sub_dir.name.endswith('_b1'):
                                    file_dir = sub_dir
                                    break
                            break
                        else:
                            # 如果直接匹配失败，尝试查找包含file_id的目录（处理_b1后缀等情况）
                            for sub_dir in library_dir.iterdir():
                                if sub_dir.is_dir() and file_id in sub_dir.name:
                                    file_dir = sub_dir
                                    # 检查是否有子目录（如 {file_id}_b1）
                                    for sub_sub_dir in sub_dir.iterdir():
                                        if sub_sub_dir.is_dir() and sub_sub_dir.name.endswith('_b1'):
                                            file_dir = sub_sub_dir
                                            break
                                    break
                            if file_dir:
                                break
            
            if not file_dir:
                return jsonify({'error': '文件目录不存在'}), 404
            
            # 图片文件在 file_id/images 子目录中
            image_file = file_dir / "images" / image_path
            
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
            # 添加 CORS 头部支持和缓存头
            response = send_from_directory(str(image_file.parent), image_path)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            
            # 设置缓存头，让浏览器缓存图片1年
            response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1年
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
                print(f"文库目录不存在: {library_dir}")
                return jsonify({'data': []})
            
            files = []
            print(f"扫描文库目录: {library_dir}")
            
            # 直接查找文件目录（不再通过批次目录）
            for file_dir in library_dir.iterdir():
                if file_dir.is_dir() and file_dir.name != 'info.json':
                    print(f"检查文件目录: {file_dir}")
                    
                    # 查找实际的文件目录（可能在子目录中，如 {file_id}_b1）
                    actual_file_dir = file_dir
                    filename_info_file = file_dir / 'filename_info.json'
                    
                    # 如果当前目录没有filename_info.json，查找子目录
                    if not filename_info_file.exists():
                        for sub_dir in file_dir.iterdir():
                            if sub_dir.is_dir():
                                potential_info_file = sub_dir / 'filename_info.json'
                                if potential_info_file.exists():
                                    actual_file_dir = sub_dir
                                    filename_info_file = potential_info_file
                                    print(f"在子目录中找到文件信息: {sub_dir}")
                                    break
                    
                    if filename_info_file.exists():
                        try:
                            with open(filename_info_file, 'r', encoding='utf-8') as f:
                                file_info = json.load(f)
                            
                            files.append({
                                'id': file_dir.name,  # 使用父目录名作为ID
                                'name': file_info.get('original_filename', file_dir.name),
                                'created_at': file_info.get('upload_time', datetime.now().isoformat()),
                                'size': file_info.get('file_size', 0),
                                'status': file_info.get('status', 'processed'),
                                'is_ocr': file_info.get('is_ocr', True),
                                'enable_formula': file_info.get('enable_formula', False)
                            })
                            print(f"添加文件: {file_info.get('original_filename', file_dir.name)}")
                        except Exception as e:
                            print(f"读取文件信息失败: {e}")
                            continue
                    else:
                        # 没有filename_info.json文件，使用fallback逻辑
                        print(f"目录 {file_dir.name} 没有filename_info.json，使用fallback逻辑")
                        
                        # 从目录名推断原始文件名
                        original_filename = file_dir.name
                        if '.pdf-' in file_dir.name:
                            # 格式如: 2503.08726v1.pdf-485102e2-86ed-41db-88b2-739c99519177
                            # 提取PDF文件名部分
                            original_filename = file_dir.name.split('.pdf-')[0] + '.pdf'
                        
                        # 检查是否有full.md文件来确定处理状态
                        full_md_file = actual_file_dir / 'full.md'
                        status = 'processed' if full_md_file.exists() else 'processing'
                        
                        # 获取文件大小（如果有origin PDF文件）
                        file_size = 0
                        for file in actual_file_dir.iterdir():
                            if file.is_file() and file.name.endswith('_origin.pdf'):
                                file_size = file.stat().st_size
                                break
                        
                        files.append({
                            'id': file_dir.name,
                            'name': original_filename,
                            'created_at': datetime.now().isoformat(),  # 使用当前时间作为fallback
                            'size': file_size,
                            'status': status,
                            'is_ocr': True,
                            'enable_formula': False
                        })
                        print(f"添加文件(fallback): {original_filename}")
            
            print(f"找到 {len(files)} 个文件")
            # 按上传时间排序
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
            
            # 查找文件目录（直接在文库下）
            file_dir = None
            # 先尝试直接匹配file_id
            potential_file_dir = library_dir / file_id
            if potential_file_dir.exists():
                file_dir = potential_file_dir
            else:
                # 如果直接匹配失败，尝试查找包含file_id的目录（处理_b1后缀等情况）
                for sub_dir in library_dir.iterdir():
                    if sub_dir.is_dir() and file_id in sub_dir.name:
                        file_dir = sub_dir
                        break
            
            if not file_dir or not file_dir.exists():
                return jsonify({'error': '文件不存在'}), 404
            
            # 删除文件目录及其所有内容
            shutil.rmtree(file_dir)
            
            # 检查文库文件夹是否为空，如果为空则删除（但保留默认文库）
            if (library_dir.exists() and 
                not any(library_dir.iterdir()) and 
                library_dir.name != 'default'):
                shutil.rmtree(library_dir)
                print(f"删除空文库文件夹: {library_dir}")
            
            print(f"删除文件成功: {file_dir}")
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