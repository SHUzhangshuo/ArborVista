import requests
import os
import zipfile
import time
import uuid
import shutil
from urllib.parse import urlparse
from pathlib import Path

class MinerUAPI:
    """MinerU API客户端"""
    
    def __init__(self, token, base_url="https://mineru.net/api/v4"):
        self.token = token
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        
        # 配置请求会话，禁用代理
        self.session = requests.Session()
        self.session.proxies = {
            'http': None,
            'https': None
        }
        self.session.verify = True
        self.session.timeout = 30
    
    def process_files_batch(self, file_paths, output_dir, batch_index=0, max_files_per_batch=200, language="en", is_ocr=True, enable_formula=True, enable_table=True, layout_model="doclayout_yolo"):
        """批量处理文件 - 严格按照test_input.py和test_output.py的逻辑"""
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
                
                # 构建文件数据
                files_data = []
                for file_path in batch_files:
                    if os.path.exists(file_path):
                        files_data.append({
                            "name": os.path.basename(file_path),
                            "is_ocr": is_ocr,
                            "data_id": f"{os.path.splitext(os.path.basename(file_path))[0]}_b{batch_idx // max_files_per_batch + 1}",
                            "language": language,
                        })
                
                if not files_data:
                    print(f"批次 {batch_idx // max_files_per_batch + 1} 没有有效文件")
                    continue
                
                # 提交批次任务
                batch_result = self._submit_single_batch(files_data, batch_files, enable_formula, language, layout_model, enable_table)
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
    
    def _submit_single_batch(self, files_data, file_paths, enable_formula, language, layout_model, enable_table):
        """提交单个批次任务"""
        try:
            # 获取上传URL
            response = self.session.post(
                f"{self.base_url}/file-urls/batch",
                headers=self.headers,
                json={
                    "enable_formula": enable_formula,
                    "language": language,
                    "layout_model": layout_model,
                    "enable_table": enable_table,
                    "files": files_data
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
            
            # 分析处理状态
            data_list = batch_data['data']['extract_result']
            total_files = len(data_list)
            completed_files = len([item for item in data_list if item.get('state') == 'done'])
            failed_files = len([item for item in data_list if item.get('state') == 'failed'])
            processing_files = len([item for item in data_list if item.get('state') == 'processing'])
            
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
            
            # 构建文件数据
            files_data = [{
                "name": os.path.basename(file_path),
                "is_ocr": is_ocr,
                "data_id": f"{os.path.splitext(os.path.basename(file_path))[0]}_b{batch_index + 1}",
                "language": language,
            } for file_path in batch_files]
            
            print(f"正在处理第 {batch_index + 1} 批次（共 {len(batch_files)} 个文件）")
            
            # 获取上传URL
            response = self.session.post(
                f"{self.base_url}/file-urls/batch",
                headers=self.headers,
                json={
                    "enable_formula": enable_formula,
                    "language": language,
                    "layout_model": layout_model,
                    "enable_table": enable_table,
                    "files": files_data
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
                    original_name = item['file_name']
                    data_id = item['data_id']
                    
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

    def process_file(self, file_path, output_dir, is_ocr=True, enable_formula=False, max_wait_time=300):
        """处理文件的完整流程"""
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
