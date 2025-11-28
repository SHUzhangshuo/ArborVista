import requests
import os
import zipfile
import time
import uuid
import shutil
import subprocess
from urllib.parse import urlparse
from pathlib import Path

class MinerUAPI:
    """MinerU API客户端 - 支持在线API和本地调用"""
    
    def __init__(self, token=None, base_url="https://mineru.net/api/v4", use_local=False, local_url="http://127.0.0.1:30000"):
        """
        初始化MinerU客户端
        
        Args:
            token: MinerU API token (在线模式需要)
            base_url: MinerU API base URL (默认: https://mineru.net/api/v4)
            use_local: 是否使用本地vLLM后端 (默认: False)
            local_url: 本地vLLM后端URL (默认: http://127.0.0.1:30000)
        """
        self.use_local = use_local
        self.local_url = local_url
        
        if not use_local:
            # Online mode
            self.token = token or os.environ.get("MINERU_API_TOKEN")
            if not self.token:
                raise ValueError(
                    "MINERU_API_TOKEN is required for online mode. "
                    "Set it as environment variable or pass as parameter."
                )
            self.base_url = base_url
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}"
            }
            
            # 配置请求会话，禁用代理
            self.session = requests.Session()
            self.session.proxies = {
                'http': None,
                'https': None
            }
            self.session.verify = True
            self.session.timeout = 30
        else:
            # Local mode - check if mineru command is available
            try:
                result = subprocess.run(
                    ["mineru", "-v"],
                    capture_output=True,
                    check=True,
                    timeout=10,
                    text=True
                )
            except FileNotFoundError:
                raise ValueError(
                    "MinerU command not found. Please install MinerU first:\n"
                    "  1. Install uv: pip install uv\n"
                    "  2. Create conda environment: conda create -n mineru python=3.12 -y\n"
                    "  3. Activate environment: conda activate mineru\n"
                    "  4. Install MinerU: uv pip install mineru"
                )
            except subprocess.TimeoutExpired:
                # If version check times out, still allow initialization
                # The actual command will fail later if mineru is not available
                pass
            except subprocess.CalledProcessError:
                raise ValueError(
                    "MinerU command check failed. Please ensure MinerU is properly installed."
                )
    
    def process_files_batch(self, file_paths, output_dir, batch_index=0, max_files_per_batch=200, language="en", is_ocr=True, enable_formula=True, enable_table=True, layout_model="doclayout_yolo", file_id_map=None, original_filename_map=None):
        """批量处理文件 - 支持在线API和本地调用
        
        Args:
            file_id_map: 文件路径到file_id的映射字典，用于本地模式时指定正确的file_id
            original_filename_map: 文件路径到原始文件名的映射字典，用于生成目录名
        """
        if self.use_local:
            # Local mode: process files sequentially
            return self._process_local_batch(
                file_paths, output_dir, is_ocr, enable_formula,
                enable_table, language, layout_model, file_id_map=file_id_map, original_filename_map=original_filename_map
            )
        else:
            # Online mode - 严格按照test_input.py和test_output.py的逻辑
            try:
                print(f"🚀 开始批量处理 {len(file_paths)} 个文件")
                
                # 第一步：生成批次ID（对应test_input.py）
                batch_result = self.generate_batch_idx(
                    file_paths=file_paths,
                    batch_index=batch_index,
                    max_files_per_batch=max_files_per_batch,
                    language=language,
                    is_ocr=is_ocr,
                    enable_formula=enable_formula,
                    enable_table=enable_table,
                    layout_model=layout_model
                )
                
                if not batch_result['success']:
                    return batch_result
                
                batch_id = batch_result['batch_id']
                print(f"✅ 批次ID生成成功: {batch_id}")
                
                # 第二步：等待处理完成 - 轮询检查状态
                print("⏳ 等待处理完成...")
                max_wait_time = 300  # 最大等待5分钟
                check_interval = 10   # 每10秒检查一次
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    # 检查批次状态
                    status_result = self.check_batch_status(batch_id)
                    if not status_result['success']:
                        print(f"❌ 检查批次状态失败: {status_result['error']}")
                        time.sleep(check_interval)
                        continue
                    
                    if status_result['is_complete']:
                        print(f"✅ 批次处理完成！成功: {status_result['completed_files']}/{status_result['total_files']}")
                        break
                    else:
                        print(f"⏳ 批次处理中: {status_result['completed_files']}/{status_result['total_files']} (已等待 {int(time.time() - start_time)} 秒)")
                        time.sleep(check_interval)
                else:
                    return {
                        'success': False,
                        'error': f'批次处理超时，等待时间超过{max_wait_time}秒'
                    }
                
                # 第三步：下载结果（对应test_output.py）
                download_result = self.download_by_batch_idx(batch_id, output_dir)
                
                if download_result['success']:
                    return {
                        'success': True,
                        'batch_id': batch_id,
                        'processed_files': download_result['processed_files'],
                        'success_count': download_result['success_count'],
                        'total_count': download_result['total_count'],
                        'output_dir': output_dir,
                        'message': f'批量处理完成，成功: {download_result["success_count"]}/{download_result["total_count"]}'
                    }
                else:
                    return download_result
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f'批量处理失败: {str(e)}'
                }
    
    def _process_local_batch(
        self,
        file_paths,
        output_dir,
        is_ocr=True,
        enable_formula=True,
        enable_table=True,
        language="en",
        layout_model="doclayout_yolo",
        file_id_map=None,
        original_filename_map=None
    ):
        """使用本地MinerU vLLM后端批量处理文件
        
        Args:
            file_paths: 文件路径列表
            output_dir: 输出目录（最终目标目录，每个文件会创建对应的子目录）
            file_id_map: 文件路径到file_id的映射字典，如果提供则使用指定的file_id
            original_filename_map: 文件路径到原始文件名的映射字典，用于生成目录名
        """
        results = []
        base_output_path = Path(output_dir)
        base_output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 开始本地批量处理 {len(file_paths)} 个文件")
        
        for idx, file_path in enumerate(file_paths, 1):
            file_path_obj = Path(file_path)
            print(f"处理文件 {idx}/{len(file_paths)}: {file_path_obj.name}")
            
            # 获取file_id：优先使用file_id_map，否则使用文件名
            if file_id_map and file_path in file_id_map:
                file_id = file_id_map[file_path]
            else:
                file_id = file_path_obj.stem
            
            # 获取原始文件名，用于生成目录名
            if original_filename_map and file_path in original_filename_map:
                original_filename = original_filename_map[file_path]
                # 去掉扩展名，将空格替换为下划线
                filename_part = Path(original_filename).stem.replace(' ', '_')
            else:
                # 如果没有原始文件名，使用保存的文件名（去掉扩展名）
                filename_part = file_path_obj.stem.replace(' ', '_')
            
            # 生成目录名：{文件名}-{file_id}
            dir_name = f"{filename_part}-{file_id}"
            
            # 为每个文件创建最终目标目录（直接输出到这里）
            file_output_dir = base_output_path / dir_name
            file_output_dir.mkdir(parents=True, exist_ok=True)
            print(f"📁 文件输出目录: {file_output_dir}")
            
            result = self._process_local(
                file_path_obj,
                file_output_dir,  # 直接输出到最终目录
                is_ocr,
                enable_formula,
                enable_table,
                language,
                layout_model,
                file_id=file_id
            )
            
            # 转换结果格式以匹配API模式的返回格式
            if result['success']:
                data_id = f"{file_id}_b1"
                
                results.append({
                    'original_name': file_path_obj.name,
                    'data_id': data_id,
                    'output_dir': str(file_output_dir),
                    'success': True
                })
            else:
                results.append({
                    'original_name': file_path_obj.name,
                    'data_id': '',
                    'output_dir': None,
                    'success': False,
                    'error': result.get('error', '处理失败')
                })
        
        success_count = sum(1 for r in results if r['success'])
        return {
            'success': success_count > 0,
            'processed_files': results,
            'success_count': success_count,
            'total_count': len(results),
            'output_dir': str(base_output_path),
            'message': f'批量处理完成，成功: {success_count}/{len(results)}'
        }
    
    def _process_local(
        self,
        input_path: Path,
        output_path: Path,
        is_ocr: bool = True,
        enable_formula: bool = True,
        enable_table: bool = True,
        language: str = "en",
        layout_model: str = "doclayout_yolo",
        file_id: str = None
    ):
        """使用本地MinerU vLLM后端处理单个文件
        
        Args:
            input_path: 输入文件路径
            output_path: 输出目录（MinerU会在这里创建子目录）
            file_id: 文件ID，如果提供则使用此ID，否则使用input_path.stem
        """
        try:
            # Build mineru command
            cmd = [
                "mineru",
                "-p", str(input_path),
                "-o", str(output_path),
                "-b", "vlm-http-client",
                "-u", self.local_url
            ]
            
            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes timeout
            )
            
            if result.returncode == 0:
                # MinerU 会在输出目录下创建子目录，需要将内容移动到目标目录
                # 检查是否有输出文件
                all_files = list(output_path.rglob("*"))
                if all_files:
                    print(f"✅ MinerU 处理完成，输出目录: {output_path}")
                    
                    # 查找所有直接子目录
                    all_subdirs = [d for d in output_path.iterdir() if d.is_dir()]
                    
                    if all_subdirs:
                        print(f"📁 发现 {len(all_subdirs)} 个子目录，开始移动内容到目标目录...")
                        
                        # 优先查找以 file_id 命名的子目录
                        target_subdir = None
                        if file_id:
                            for subdir in all_subdirs:
                                if subdir.name == file_id:
                                    target_subdir = subdir
                                    print(f"   找到 file_id 子目录: {subdir.name}")
                                    break
                        
                        # 如果没有找到 file_id 子目录，查找数字命名的子目录（如 1/, 2/）
                        if not target_subdir:
                            digit_subdirs = [d for d in all_subdirs if d.name.isdigit()]
                            if digit_subdirs:
                                target_subdir = digit_subdirs[0]
                                print(f"   找到数字子目录: {target_subdir.name}")
                        
                        # 如果找到了目标子目录，将其内容（保留目录结构）移动到主目录
                        if target_subdir:
                            print(f"   处理子目录: {target_subdir.name}")
                            
                            # 检查子目录中是否有 vlm 子目录（本地模式特有）
                            vlm_subdir = target_subdir / "vlm"
                            if vlm_subdir.exists() and vlm_subdir.is_dir():
                                print(f"   发现 vlm 子目录，处理 vlm 目录内容...")
                                # 将 vlm 目录中的内容移动到 file_id 子目录
                                for item in vlm_subdir.iterdir():
                                    target_item = target_subdir / item.name
                                    
                                    # 如果目标已存在，跳过或添加后缀
                                    if target_item.exists():
                                        if item.is_file():
                                            base_name = item.stem
                                            extension = item.suffix
                                            counter = 1
                                            while target_item.exists():
                                                target_item = target_subdir / f"{base_name}_{counter}{extension}"
                                                counter += 1
                                        else:
                                            # 如果是目录，添加后缀
                                            counter = 1
                                            while target_item.exists():
                                                target_item = target_subdir / f"{item.name}_{counter}"
                                                counter += 1
                                    
                                    # 移动文件或目录（保留目录结构）
                                    shutil.move(str(item), str(target_item))
                                    if item.is_file():
                                        print(f"      ✅ 移动文件: {item.name}")
                                    else:
                                        print(f"      ✅ 移动目录: {item.name}")
                                
                                # 删除空的 vlm 目录
                                try:
                                    if vlm_subdir.exists():
                                        shutil.rmtree(vlm_subdir)
                                        print(f"      🗑️ 删除 vlm 子目录")
                                except Exception as e:
                                    print(f"      ⚠️ 删除 vlm 子目录失败: {e}")
                            
                            # 遍历子目录中的所有内容（文件和目录）
                            for item in target_subdir.iterdir():
                                target_item = output_path / item.name
                                
                                # 如果目标已存在，跳过或添加后缀
                                if target_item.exists():
                                    if item.is_file():
                                        base_name = item.stem
                                        extension = item.suffix
                                        counter = 1
                                        while target_item.exists():
                                            target_item = output_path / f"{base_name}_{counter}{extension}"
                                            counter += 1
                                    else:
                                        # 如果是目录，添加后缀
                                        counter = 1
                                        while target_item.exists():
                                            target_item = output_path / f"{item.name}_{counter}"
                                            counter += 1
                                
                                # 移动文件或目录（保留目录结构）
                                shutil.move(str(item), str(target_item))
                                if item.is_file():
                                    print(f"   ✅ 移动文件: {item.name}")
                                else:
                                    print(f"   ✅ 移动目录: {item.name}")
                            
                            # 删除空的子目录
                            try:
                                if target_subdir.exists():
                                    shutil.rmtree(target_subdir)
                                    print(f"   🗑️ 删除子目录: {target_subdir.name}")
                            except Exception as e:
                                print(f"   ⚠️ 删除子目录失败: {e}")
                        else:
                            # 如果没有找到特定子目录，处理所有子目录（扁平化）
                            print(f"   ⚠️ 未找到特定子目录，处理所有子目录...")
                            for subdir in all_subdirs:
                                print(f"   处理子目录: {subdir.name}")
                                # 递归查找所有文件
                                for item in subdir.rglob("*"):
                                    if item.is_file():
                                        # 计算相对路径（相对于子目录）
                                        rel_path = item.relative_to(subdir)
                                        # 保留目录结构
                                        target_path = output_path / rel_path
                                        
                                        # 确保父目录存在
                                        target_path.parent.mkdir(parents=True, exist_ok=True)
                                        
                                        # 如果目标文件已存在，添加序号
                                        if target_path.exists():
                                            base_name = target_path.stem
                                            extension = target_path.suffix
                                            parent_dir = target_path.parent
                                            counter = 1
                                            while target_path.exists():
                                                target_path = parent_dir / f"{base_name}_{counter}{extension}"
                                                counter += 1
                                        
                                        # 移动文件
                                        shutil.move(str(item), str(target_path))
                                        print(f"   ✅ 移动文件: {rel_path}")
                                
                                # 删除空的子目录
                                try:
                                    if subdir.exists():
                                        shutil.rmtree(subdir)
                                        print(f"   🗑️ 删除子目录: {subdir.name}")
                                except Exception as e:
                                    print(f"   ⚠️ 删除子目录失败: {e}")
                    
                    # 再次检查目标目录中的内容
                    final_items = list(output_path.iterdir())
                    print(f"📁 最终内容数量: {len(final_items)}")
                    for item in final_items:
                        if item.is_file():
                            print(f"   📄 {item.name}")
                        else:
                            print(f"   📁 {item.name}/")
                    
                    return {
                        'success': True,
                        'input_path': str(input_path),
                        'output_dir': str(output_path),
                        'message': 'File processed successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'No markdown file found in output directory: {output_path}. '
                                f'Command stdout: {result.stdout[:200] if result.stdout else "None"}'
                    }
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                return {
                    'success': False,
                    'error': f'MinerU command failed (return code: {result.returncode}). '
                            f'Error: {error_msg}'
                }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Processing timeout (exceeded 10 minutes)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Processing failed: {str(e)}'
            }
    
    def submit_task(self, file_path, is_ocr=True, enable_formula=False, enable_table=True, language="en", layout_model="doclayout_yolo"):
        """提交单个文件处理任务到在线API"""
        if self.use_local:
            return {
                'success': False,
                'error': 'submit_task is only available in online mode. Use process_file instead.'
            }
        
        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {
                    'success': False,
                    'error': f'File not found: {file_path}'
                }
            
            # Get upload URL
            response = self.session.post(
                f"{self.base_url}/file-urls",
                headers=self.headers,
                json={
                    "name": file_path_obj.name,
                    "is_ocr": is_ocr,
                    "enable_formula": enable_formula,
                    "enable_table": enable_table,
                    "language": language,
                    "layout_model": layout_model
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Request failed with status {response.status_code}'
                }
            
            result = response.json()
            if result.get("code") != 0:
                return {
                    'success': False,
                    'error': result.get("msg", "Unknown error")
                }
            
            # Upload file
            upload_url = result["data"]["file_url"]
            task_id = result["data"]["task_id"]
            
            with open(file_path_obj, 'rb') as f:
                upload_response = self.session.put(upload_url, data=f)
                if upload_response.status_code not in [200, 201]:
                    return {
                        'success': False,
                        'error': f'Upload failed with status {upload_response.status_code}'
                    }
            
            return {
                'success': True,
                'task_id': task_id
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Submit task failed: {str(e)}'
            }
    
    def check_task_status(self, task_id):
        """检查任务状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/extract/task/{task_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    return {
                        'success': True,
                        'state': data.get('state'),
                        'zip_url': data.get('full_zip_url'),
                        'error_msg': data.get('err_msg', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('msg', '获取任务状态失败')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'检查任务状态失败: {str(e)}'
            }
    
    def download_and_extract_result(self, zip_url, output_dir):
        """下载并解压结果文件"""
        try:
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 从URL中提取文件名
            parsed_url = urlparse(zip_url)
            filename = os.path.basename(parsed_url.path)
            if not filename.endswith('.zip'):
                filename = f"mineru_result_{int(time.time())}.zip"
            
            zip_path = output_path / filename
            
            print(f"开始下载文件: {zip_url}")
            print(f"保存到: {zip_path}")
            
            # 下载文件
            response = self.session.get(zip_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\r下载进度: {percent:.1f}%", end='', flush=True)
            
            print(f"\n下载完成: {zip_path}")
            
            # 解压文件
            extract_dir = output_path / filename.replace('.zip', '')
            print(f"开始解压到: {extract_dir}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"解压完成: {extract_dir}")
            
            # 查找markdown文件
            md_files = list(extract_dir.rglob("*.md"))
            if md_files:
                # 将markdown文件移动到输出目录的根目录
                md_file = md_files[0]
                target_md = extract_dir / "result.md"
                md_file.rename(target_md)
                print(f"找到markdown文件: {target_md}")
            
            # 查找图片文件
            image_files = list(extract_dir.rglob("*.jpg")) + list(extract_dir.rglob("*.png"))
            if image_files:
                # 创建images目录
                images_dir = extract_dir / "images"
                images_dir.mkdir(exist_ok=True)
                
                # 移动图片文件到images目录
                for img_file in image_files:
                    target_img = images_dir / img_file.name
                    img_file.rename(target_img)
                    print(f"移动图片文件: {target_img}")
            
            return {
                'success': True,
                'extract_dir': str(extract_dir),
                'md_file': str(extract_dir / "result.md") if md_files else None,
                'images_dir': str(extract_dir / "images") if image_files else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'下载或解压失败: {str(e)}'
            }
    
    def get_batch_results(self, batch_id, output_dir):
        """获取批量处理结果"""
        try:
            print(f"📦 获取批量处理结果: {batch_id}")
            
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 获取批量结果
            response = self.session.get(
                f"{self.base_url}/extract-results/batch/{batch_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }
            
            batch_data = response.json()
            if batch_data.get('code') != 0:
                return {
                    'success': False,
                    'error': batch_data.get('msg', '获取批量结果失败')
                }
            
            # 处理结果数据
            data_list = batch_data['data']['extract_result']
            processed_files = []
            
            for item in data_list:
                if item.get('state') == 'done' and 'full_zip_url' in item:
                    zip_url = item['full_zip_url']
                    original_name = item['file_name']
                    
                    # 生成最终路径
                    base_name = os.path.splitext(original_name)[0]
                    final_filename = f"{base_name}.md"
                    output_file_path = output_path / final_filename
                    
                    try:
                        # 创建临时目录
                        temp_dir = output_path / f"temp_{item['data_id']}"
                        temp_dir.mkdir(exist_ok=True)
                        
                        # 下载ZIP文件
                        zip_response = self.session.get(zip_url, stream=True)
                        zip_response.raise_for_status()
                        
                        # 保存临时ZIP
                        zip_name = os.path.basename(urlparse(zip_url).path)
                        zip_path = temp_dir / zip_name
                        
                        with open(zip_path, 'wb') as f:
                            for chunk in zip_response.iter_content(1024 * 1024):  # 1MB chunks
                                f.write(chunk)
                        
                        # 解压并处理文件
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            # 搜索full.md文件
                            target_file = None
                            for file_info in zip_ref.infolist():
                                if os.path.basename(file_info.filename) == 'full.md':
                                    target_file = file_info
                                    break
                            
                            if target_file:
                                # 解压到临时目录
                                zip_ref.extract(target_file, temp_dir)
                                
                                # 构建完整路径
                                extracted_path = temp_dir / target_file.filename
                                
                                # 移动并重命名
                                shutil.move(str(extracted_path), str(output_file_path))
                                print(f"✅ 成功处理：{original_name} -> {output_file_path}")
                                
                                processed_files.append({
                                    'original_name': original_name,
                                    'output_path': str(output_file_path),
                                    'success': True
                                })
                            else:
                                print(f"⚠️ 警告：{zip_name} 中未找到full.md文件")
                                processed_files.append({
                                    'original_name': original_name,
                                    'output_path': None,
                                    'success': False,
                                    'error': '未找到full.md文件'
                                })
                        
                    except requests.exceptions.RequestException as e:
                        print(f"❌ 下载失败：{original_name} | 错误：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'output_path': None,
                            'success': False,
                            'error': f'下载失败: {str(e)}'
                        })
                    except zipfile.BadZipFile:
                        print(f"❌ 损坏的ZIP文件：{original_name}")
                        processed_files.append({
                            'original_name': original_name,
                            'output_path': None,
                            'success': False,
                            'error': '损坏的ZIP文件'
                        })
                    except Exception as e:
                        print(f"❌ 处理异常：{original_name} | 错误类型：{type(e).__name__} | 详情：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'output_path': None,
                            'success': False,
                            'error': f'处理异常: {str(e)}'
                        })
                    finally:
                        # 清理临时文件
                        if temp_dir.exists():
                            shutil.rmtree(temp_dir)
            
            return {
                'success': True,
                'processed_files': processed_files,
                'output_dir': str(output_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'获取批量结果失败: {str(e)}'
            }
    
    def submit_batch_task(self, file_paths, is_ocr=True, enable_formula=True, language="en", layout_model="doclayout_yolo", enable_table=True, max_files_per_batch=200):
        """提交批量处理任务"""
        try:
            print(f"📦 提交批量处理任务，文件数量: {len(file_paths)}")
            
            # 分批处理文件
            all_batch_ids = []
            total_files = len(file_paths)
            
            for batch_idx in range(0, total_files, max_files_per_batch):
                batch_files = file_paths[batch_idx:batch_idx + max_files_per_batch]
                print(f"处理第 {batch_idx // max_files_per_batch + 1} 批次，文件数量: {len(batch_files)}")
                
                # 构建文件数据 - 根据最新API文档格式
                files_data = []
                for file_path in batch_files:
                    if os.path.exists(file_path):
                        file_name = os.path.basename(file_path)
                        files_data.append({
                            "name": file_name,
                            "is_ocr": is_ocr,
                            "data_id": f"{os.path.splitext(file_name)[0]}_b{batch_idx // max_files_per_batch + 1}",
                        })
                
                if not files_data:
                    print(f"批次 {batch_idx // max_files_per_batch + 1} 没有有效文件")
                    continue
                
                # 提交批次任务 - 默认使用vlm模型
                batch_result = self._submit_single_batch(files_data, batch_files, enable_formula, language, layout_model, enable_table, model_version="vlm")
                if batch_result['success']:
                    all_batch_ids.append(batch_result['batch_id'])
                    print(f"✅ 批次 {batch_idx // max_files_per_batch + 1} 提交成功，批次ID: {batch_result['batch_id']}")
                else:
                    print(f"❌ 批次 {batch_idx // max_files_per_batch + 1} 提交失败: {batch_result['error']}")
            
            if all_batch_ids:
                return {
                    'success': True,
                    'batch_ids': all_batch_ids,
                    'message': f'成功提交 {len(all_batch_ids)} 个批次'
                }
            else:
                return {
                    'success': False,
                    'error': '所有批次提交失败'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'提交批量任务失败: {str(e)}'
            }
    
    def _submit_single_batch(self, files_data, file_paths, enable_formula, language, layout_model, enable_table, model_version="vlm"):
        """提交单个批次任务"""
        try:
            # 获取上传URL - 根据最新API文档
            response = self.session.post(
                f"{self.base_url}/file-urls/batch",
                headers=self.headers,
                json={
                    "files": files_data,
                    "model_version": model_version,
                    "enable_formula": enable_formula,
                    "enable_table": enable_table,
                    "language": language
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'请求失败，状态码：{response.status_code}'
                }
            
            result = response.json()
            if result["code"] != 0:
                return {
                    'success': False,
                    'error': f'申请失败，原因：{result.get("msg", "未知错误")}'
                }
            
            # 上传文件
            batch_id = result["data"]["batch_id"]
            urls = result["data"]["file_urls"]
            success_count = 0
            
            for idx, (url, file_path) in enumerate(zip(urls, file_paths)):
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        res = self.session.put(url, data=f)
                        if res.status_code in [200, 201]:
                            success_count += 1
                        else:
                            print(f"❌ 失败文件：{os.path.basename(file_path)}，状态码：{res.status_code}")
            
            print(f"📤 批次上传完成 | 成功：{success_count}/{len(file_paths)} | 批次ID：{batch_id}")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'uploaded_count': success_count,
                'total_count': len(file_paths)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'提交批次失败: {str(e)}'
            }
    
    def check_batch_status(self, batch_id):
        """检查批量处理状态"""
        try:
            response = self.session.get(
                f"{self.base_url}/extract-results/batch/{batch_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }
            
            batch_data = response.json()
            if batch_data.get('code') != 0:
                return {
                    'success': False,
                    'error': batch_data.get('msg', '获取批量状态失败')
                }
            
            # 分析处理状态 - 根据最新API文档
            data_list = batch_data['data']['extract_result']
            total_files = len(data_list)
            completed_files = len([item for item in data_list if item.get('state') == 'done'])
            failed_files = len([item for item in data_list if item.get('state') == 'failed'])
            processing_files = len([item for item in data_list if item.get('state') in ['pending', 'running', 'converting', 'waiting-file']])
            
            return {
                'success': True,
                'batch_id': batch_id,
                'total_files': total_files,
                'completed_files': completed_files,
                'failed_files': failed_files,
                'processing_files': processing_files,
                'is_complete': completed_files + failed_files == total_files,
                'data_list': data_list
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'检查批量状态失败: {str(e)}'
            }
    
    def download_batch_results(self, batch_id, output_dir):
        """下载批量处理结果"""
        try:
            print(f"📥 下载批量处理结果: {batch_id}")
            
            # 检查批量状态
            status_result = self.check_batch_status(batch_id)
            if not status_result['success']:
                return status_result
            
            if not status_result['is_complete']:
                return {
                    'success': False,
                    'error': f'批量处理未完成，已完成: {status_result["completed_files"]}/{status_result["total_files"]}'
                }
            
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            data_list = status_result['data_list']
            processed_files = []
            
            for item in data_list:
                if item.get('state') == 'done' and 'full_zip_url' in item:
                    zip_url = item['full_zip_url']
                    original_name = item['file_name']
                    data_id = item['data_id']
                    
                    # 为每个文件创建独立的目录，使用data_id作为目录名
                    file_output_dir = output_path / data_id
                    file_output_dir.mkdir(exist_ok=True)
                    
                    try:
                        # 创建临时目录
                        temp_dir = output_path / f"temp_{data_id}"
                        temp_dir.mkdir(exist_ok=True)
                        
                        # 下载ZIP文件
                        zip_response = self.session.get(zip_url, stream=True)
                        zip_response.raise_for_status()
                        
                        # 保存临时ZIP
                        zip_name = os.path.basename(urlparse(zip_url).path)
                        zip_path = temp_dir / zip_name
                        
                        with open(zip_path, 'wb') as f:
                            for chunk in zip_response.iter_content(1024 * 1024):  # 1MB chunks
                                f.write(chunk)
                        
                        # 解压整个ZIP文件到目标目录
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(file_output_dir)
                            print(f"✅ 成功处理：{original_name} -> {file_output_dir}")
                        
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': str(file_output_dir),
                            'success': True
                        })
                        
                    except requests.exceptions.RequestException as e:
                        print(f"❌ 下载失败：{original_name} | 错误：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': f'下载失败: {str(e)}'
                        })
                    except zipfile.BadZipFile:
                        print(f"❌ 损坏的ZIP文件：{original_name}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': '损坏的ZIP文件'
                        })
                    except Exception as e:
                        print(f"❌ 处理异常：{original_name} | 错误类型：{type(e).__name__} | 详情：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': f'处理异常: {str(e)}'
                        })
                    finally:
                        # 清理临时文件
                        if temp_dir.exists():
                            shutil.rmtree(temp_dir)
                elif item.get('state') == 'failed':
                    print(f"❌ 文件处理失败：{item.get('file_name', '未知文件')}")
                    processed_files.append({
                        'original_name': item.get('file_name', '未知文件'),
                        'data_id': item.get('data_id', ''),
                        'output_dir': None,
                        'success': False,
                        'error': '文件处理失败'
                    })
            
            return {
                'success': True,
                'batch_id': batch_id,
                'processed_files': processed_files,
                'output_dir': str(output_path)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'下载批量结果失败: {str(e)}'
            }
    
    def process_batch_files(self, file_paths, output_dir, is_ocr=True, enable_formula=True, language="en", max_wait_time=1800):
        """处理批量文件的完整流程"""
        try:
            print(f"🚀 开始批量处理 {len(file_paths)} 个文件")
            
            # 1. 提交批量任务
            submit_result = self.submit_batch_task(
                file_paths, 
                is_ocr=is_ocr, 
                enable_formula=enable_formula, 
                language=language
            )
            if not submit_result['success']:
                return submit_result
            
            batch_ids = submit_result['batch_ids']
            print(f"📋 成功提交 {len(batch_ids)} 个批次")
            
            # 2. 等待所有批次完成
            print("⏳ 等待批量处理完成...")
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                all_complete = True
                
                for batch_id in batch_ids:
                    status_result = self.check_batch_status(batch_id)
                    if not status_result['success']:
                        print(f"❌ 检查批次 {batch_id} 状态失败: {status_result['error']}")
                        continue
                    
                    if not status_result['is_complete']:
                        all_complete = False
                        print(f"⏳ 批次 {batch_id} 处理中: {status_result['completed_files']}/{status_result['total_files']}")
                
                if all_complete:
                    print("✅ 所有批次处理完成")
                    break
                
                # 等待30秒后再次检查
                time.sleep(30)
            
            if not all_complete:
                return {
                    'success': False,
                    'error': f'批量处理超时，等待时间超过{max_wait_time}秒'
                }
            
            # 3. 下载所有批次的结果
            all_processed_files = []
            for batch_id in batch_ids:
                download_result = self.download_batch_results(batch_id, output_dir)
                if download_result['success']:
                    all_processed_files.extend(download_result['processed_files'])
                else:
                    print(f"❌ 下载批次 {batch_id} 结果失败: {download_result['error']}")
            
            success_count = len([f for f in all_processed_files if f['success']])
            total_count = len(all_processed_files)
            
            return {
                'success': True,
                'processed_files': all_processed_files,
                'success_count': success_count,
                'total_count': total_count,
                'output_dir': output_dir,
                'message': f'批量处理完成，成功: {success_count}/{total_count}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'批量处理失败: {str(e)}'
            }

    def generate_batch_idx(self, file_paths, batch_index=0, max_files_per_batch=200, language="ch", is_ocr=True, enable_formula=True, enable_table=True, layout_model="doclayout_yolo"):
        """生成批次ID - 对应test_input.py的功能"""
        try:
            # 检查文件是否存在
            valid_files = []
            for file_path in file_paths:
                if os.path.exists(file_path):
                    valid_files.append(file_path)
                else:
                    print(f"⚠️ 文件不存在，跳过: {file_path}")
            
            if not valid_files:
                return {
                    'success': False,
                    'error': '没有有效的文件可处理'
                }
            
            print(f"找到 {len(valid_files)} 个有效文件")
            print(f"处理第 {batch_index} 批次")
            
            # 计算批次文件范围
            batch_idx = max_files_per_batch * batch_index
            batch_files = valid_files[batch_idx : batch_idx + max_files_per_batch]
            
            if not batch_files:
                return {
                    'success': False,
                    'error': f'第 {batch_index} 批次没有文件可处理'
                }
            
            # 构建文件数据 - 根据最新API文档格式
            files_data = [{
                "name": os.path.basename(file_path),
                "is_ocr": is_ocr,
                "data_id": f"{os.path.splitext(os.path.basename(file_path))[0]}_b{batch_index + 1}",
            } for file_path in batch_files]
            
            print(f"正在处理第 {batch_index + 1} 批次（共 {len(batch_files)} 个文件）")
            
            # 获取上传URL - 根据最新API文档
            response = self.session.post(
                f"{self.base_url}/file-urls/batch",
                headers=self.headers,
                json={
                    "files": files_data,
                    "model_version": "vlm",  # 默认使用vlm，也可以使用pipeline
                    "enable_formula": enable_formula,
                    "enable_table": enable_table,
                    "language": language
                }
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'请求失败，状态码：{response.status_code}'
                }
            
            result = response.json()
            if result["code"] != 0:
                return {
                    'success': False,
                    'error': f'申请失败，原因：{result.get("msg", "未知错误")}'
                }
            
            # 上传文件
            batch_id = result["data"]["batch_id"]
            urls = result["data"]["file_urls"]
            success_count = 0
            
            for idx, (url, file_path) in enumerate(zip(urls, batch_files)):
                with open(file_path, 'rb') as f:
                    res = self.session.put(url, data=f)
                    if res.status_code in [200, 201]:
                        success_count += 1
                    else:
                        print(f"失败文件：{os.path.basename(file_path)}，状态码：{res.status_code}")
            
            print(f"第 {batch_index + 1} 批次完成 | 成功：{success_count}/{len(batch_files)} | 批次ID：{batch_id}")
            
            return {
                'success': True,
                'batch_id': batch_id,
                'uploaded_count': success_count,
                'total_count': len(batch_files),
                'message': f'第 {batch_index + 1} 批次提交成功，批次ID: {batch_id}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'生成批次ID失败: {str(e)}'
            }
    
    def download_by_batch_idx(self, batch_id, output_dir):
        """利用批次ID下载结果 - 对应test_output.py的功能"""
        try:
            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"开始下载批次 {batch_id} 的结果...")
            
            # 先检查批次状态，确保所有文件都处理完成
            status_result = self.check_batch_status(batch_id)
            if not status_result['success']:
                return {
                    'success': False,
                    'error': f'检查批次状态失败: {status_result["error"]}'
                }
            
            if not status_result['is_complete']:
                return {
                    'success': False,
                    'error': f'批次处理未完成，已完成: {status_result["completed_files"]}/{status_result["total_files"]}，请稍后重试'
                }
            
            # 获取批次结果
            response = self.session.get(
                f"{self.base_url}/extract-results/batch/{batch_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP错误: {response.status_code}'
                }
            
            batch_data = response.json()
            if batch_data.get('code') != 0:
                return {
                    'success': False,
                    'error': batch_data.get('msg', '获取批次结果失败')
                }
            
            # 正确访问数据路径
            data_list = batch_data['data']['extract_result']
            
            processed_files = []
            
            for item in data_list:
                if item.get('state') == 'done' and 'full_zip_url' in item:
                    zip_url = item['full_zip_url']
                    original_name = item.get('file_name', '')
                    data_id = item.get('data_id', '')
                    
                    # 为每个文件创建独立的目录，使用data_id作为目录名
                    file_output_dir = os.path.join(output_dir, data_id)
                    os.makedirs(file_output_dir, exist_ok=True)
                    
                    try:
                        # 创建临时目录
                        temp_dir = os.path.join(output_dir, f"temp_{data_id}")
                        os.makedirs(temp_dir, exist_ok=True)
                        
                        # 下载ZIP文件
                        zip_response = self.session.get(zip_url, stream=True)
                        zip_response.raise_for_status()
                        
                        # 保存临时ZIP
                        zip_name = os.path.basename(urlparse(zip_url).path)
                        zip_path = os.path.join(temp_dir, zip_name)
                        with open(zip_path, 'wb') as f:
                            for chunk in zip_response.iter_content(1024 * 1024):  # 1MB chunks
                                f.write(chunk)
                        
                        # 解压整个ZIP文件到目标目录
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(file_output_dir)
                            print(f"成功处理：{original_name} -> {file_output_dir}")
                        
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': file_output_dir,
                            'success': True
                        })
                        
                    except requests.exceptions.RequestException as e:
                        print(f"下载失败：{original_name} | 错误：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': f'下载失败: {str(e)}'
                        })
                    except zipfile.BadZipFile:
                        print(f"损坏的ZIP文件：{original_name}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': '损坏的ZIP文件'
                        })
                    except Exception as e:
                        print(f"处理异常：{original_name} | 错误类型：{type(e).__name__} | 详情：{str(e)}")
                        processed_files.append({
                            'original_name': original_name,
                            'data_id': data_id,
                            'output_dir': None,
                            'success': False,
                            'error': f'处理异常: {str(e)}'
                        })
                    finally:
                        # 清理临时文件
                        if os.path.exists(temp_dir):
                            shutil.rmtree(temp_dir)
                elif item.get('state') == 'running':
                    print(f"⏳ 文件仍在处理中：{item.get('file_name', '未知文件')} - 状态: {item.get('state')}")
                    processed_files.append({
                        'original_name': item.get('file_name', '未知文件'),
                        'data_id': item.get('data_id', ''),
                        'output_dir': None,
                        'success': False,
                        'error': '文件仍在处理中，请稍后重试'
                    })
                else:
                    print(f"文件处理状态异常：{item.get('file_name', '未知文件')} - {item.get('state', '未知状态')}")
                    processed_files.append({
                        'original_name': item.get('file_name', '未知文件'),
                        'data_id': item.get('data_id', ''),
                        'output_dir': None,
                        'success': False,
                        'error': f'处理状态异常: {item.get("state", "未知状态")}'
                    })
            
            success_count = len([f for f in processed_files if f['success']])
            total_count = len(processed_files)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'processed_files': processed_files,
                'success_count': success_count,
                'total_count': total_count,
                'output_dir': output_dir,
                'message': f'批次 {batch_id} 下载完成，成功: {success_count}/{total_count}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'利用批次ID下载失败: {str(e)}'
            }

    def process_file(self, file_path, output_dir, is_ocr=True, enable_formula=False, enable_table=True, language="en", layout_model="doclayout_yolo", max_wait_time=300):
        """处理文件的完整流程 - 支持在线API和本地调用"""
        if self.use_local:
            # Local mode
            return self._process_local(
                Path(file_path),
                Path(output_dir),
                is_ocr,
                enable_formula,
                enable_table,
                language,
                layout_model
            )
        else:
            # Online mode
            try:
                # 1. 提交任务
                print("提交文件处理任务...")
                submit_result = self.submit_task(file_path, is_ocr, enable_formula)
                if not submit_result['success']:
                    return submit_result
                
                task_id = submit_result['task_id']
                print(f"任务ID: {task_id}")
                
                # 2. 轮询任务状态
                print("等待任务完成...")
                start_time = time.time()
                
                while time.time() - start_time < max_wait_time:
                    status_result = self.check_task_status(task_id)
                    if not status_result['success']:
                        return status_result
                    
                    state = status_result['state']
                    print(f"任务状态: {state}")
                    
                    if state == 'done':
                        zip_url = status_result['zip_url']
                        if zip_url:
                            # 3. 下载并解压结果
                            print("任务完成，开始下载结果...")
                            return self.download_and_extract_result(zip_url, output_dir)
                        else:
                            return {
                                'success': False,
                                'error': '任务完成但未找到下载链接'
                            }
                    elif state == 'failed':
                        return {
                            'success': False,
                            'error': f'任务失败: {status_result.get("error_msg", "未知错误")}'
                        }
                    
                    # 等待5秒后再次检查
                    time.sleep(5)
                
                return {
                    'success': False,
                    'error': f'任务超时，等待时间超过{max_wait_time}秒'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'处理文件失败: {str(e)}'
                }
