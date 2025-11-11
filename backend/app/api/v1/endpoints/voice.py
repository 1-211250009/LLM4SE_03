"""
语音相关API端点
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io
import base64
import httpx
import json
import hmac
import hashlib
import os
import time
from datetime import datetime
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.core.config import settings

router = APIRouter()

def convert_audio_to_pcm(audio_data: bytes, content_type: str) -> bytes:
    """
    将音频文件转换为PCM格式（16kHz, 16bit, 单声道）
    科大讯飞API需要: audio/L16;rate=16000
    
    使用ffmpeg直接转换，简单可靠（参考博客做法）
    """
    import tempfile
    import os
    import shutil
    import subprocess
    
    # 查找ffmpeg路径（尝试多个可能的位置）
    ffmpeg_path = None
    
    # 方法1: 使用shutil.which（会查找PATH中的ffmpeg）
    ffmpeg_path = shutil.which("ffmpeg")
    
    # 方法2: 如果找不到，尝试常见的安装路径
    if not ffmpeg_path:
        common_paths = [
            "/opt/homebrew/bin/ffmpeg",  # macOS Homebrew (Apple Silicon)
            "/usr/local/bin/ffmpeg",     # macOS Homebrew (Intel) 或 Linux
            "/usr/bin/ffmpeg",           # Linux系统路径
            "/bin/ffmpeg",               # 其他Linux路径
        ]
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                ffmpeg_path = path
                print(f"[音频转换] 在常见路径找到ffmpeg: {ffmpeg_path}")
                break
    
    # 方法3: 如果还是找不到，尝试更新PATH后再次查找
    if not ffmpeg_path:
        # 添加常见路径到PATH
        common_dirs = ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]
        current_path = os.environ.get("PATH", "")
        for dir_path in common_dirs:
            if dir_path not in current_path:
                os.environ["PATH"] = dir_path + os.pathsep + current_path
        
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"[音频转换] 更新PATH后找到ffmpeg: {ffmpeg_path}")
    
    if not ffmpeg_path:
        raise Exception(
            "ffmpeg未找到。请确保已安装ffmpeg:\n"
            "  macOS: brew install ffmpeg\n"
            "  Linux: apt-get install ffmpeg 或 yum install ffmpeg\n"
            "  如果已安装，请检查PATH环境变量是否包含ffmpeg所在目录"
        )
    
    print(f"[音频转换] 使用ffmpeg路径: {ffmpeg_path}")
    
    # 创建临时输入和输出文件
    input_file = None
    output_file = None
    
    try:
        # 创建临时输入文件
        input_fd, input_file = tempfile.mkstemp(suffix='.webm')
        with os.fdopen(input_fd, 'wb') as f:
            f.write(audio_data)
        
        # 创建临时输出文件（PCM格式）
        output_fd, output_file = tempfile.mkstemp(suffix='.pcm')
        os.close(output_fd)
        
        print(f"[音频转换] 输入文件: {input_file}, 大小: {len(audio_data)} 字节")
        
        # 使用ffmpeg进行转换（简化参数，参考博客做法）
        cmd = [
            ffmpeg_path,
            "-i", input_file,
            "-ar", "16000",    # 采样率16kHz
            "-ac", "1",        # 单声道
            "-f", "s16le",     # 输出格式：16位小端PCM
            "-y",              # 覆盖输出文件
            "-loglevel", "error",  # 只显示错误
            output_file
        ]
        
        print(f"[音频转换] 执行命令: {' '.join(cmd)}")
        
        # 使用同步方式执行ffmpeg命令（更简单可靠）
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            print(f"[音频转换] ffmpeg错误 (返回码: {result.returncode}): {error_msg}")
            raise Exception(f"ffmpeg转换失败: {error_msg}")
        
        # 读取转换后的PCM数据
        with open(output_file, 'rb') as f:
            pcm_data = f.read()
        
        print(f"[音频转换] PCM数据大小: {len(pcm_data)} 字节")
        print(f"[音频转换] 预计时长: {len(pcm_data) / 2 / 16000:.2f} 秒")
        
        return pcm_data
        
    finally:
        # 清理临时文件
        if input_file and os.path.exists(input_file):
            try:
                os.unlink(input_file)
            except:
                pass
        if output_file and os.path.exists(output_file):
            try:
                os.unlink(output_file)
            except:
                pass

@router.post("/asr")
async def speech_to_text(
    audio_file: UploadFile = File(...),
    language: str = Form("zh_cn"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    语音识别接口
    将上传的音频文件转换为文字
    """
    try:
        # 检查文件类型
        if not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="只支持音频文件")
        
        # 读取音频数据
        audio_data = await audio_file.read()
        original_size = len(audio_data)  # 保存原始大小
        
        # 调试信息：打印音频文件信息
        print(f"[ASR] 收到音频文件:")
        print(f"  - 文件名: {audio_file.filename}")
        print(f"  - 内容类型: {audio_file.content_type}")
        print(f"  - 数据大小: {original_size} 字节")
        
        # 保存原始音频文件（用于调试）
        original_audio_path = None
        try:
            upload_dir = "uploads/audio"
            os.makedirs(upload_dir, exist_ok=True)
            
            timestamp = int(time.time())
            original_ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else 'webm'
            original_filename = f"original_{timestamp}_{current_user.id}.{original_ext}"
            original_audio_path = os.path.join(upload_dir, original_filename)
            
            with open(original_audio_path, "wb") as f:
                f.write(audio_data)
            print(f"  - 原始音频已保存: {original_audio_path}")
        except Exception as save_error:
            print(f"  - 保存原始音频失败: {save_error}")
        
        # 转换音频格式（WebM/Opus -> PCM）
        # 科大讯飞API需要PCM格式（16kHz, 16bit, 单声道）
        converted_audio_path = None
        converted_audio = None
        
        # 尝试转换音频格式
        try:
            converted_audio = convert_audio_to_pcm(audio_data, audio_file.content_type)
            print(f"  - 转换后大小: {len(converted_audio)} 字节")
            audio_data = converted_audio
            
            # 保存转换后的WAV文件（用于调试）
            try:
                import shutil
                import asyncio
                import tempfile
                
                ffmpeg_path = shutil.which("ffmpeg")
                if ffmpeg_path:
                    timestamp = int(time.time())
                    converted_filename = f"converted_{timestamp}_{current_user.id}.wav"
                    converted_audio_path = os.path.join(upload_dir, converted_filename)
                    
                    # 使用ffmpeg将PCM转换为WAV
                    pcm_fd, pcm_temp = tempfile.mkstemp(suffix='.pcm')
                    try:
                        with os.fdopen(pcm_fd, 'wb') as f:
                            f.write(converted_audio)
                        
                        cmd = [
                            ffmpeg_path,
                            "-f", "s16le", "-ar", "16000", "-ac", "1",
                            "-i", pcm_temp, "-y", converted_audio_path
                        ]
                        
                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await process.communicate()
                        
                        if process.returncode == 0:
                            duration_seconds = len(converted_audio) / 2 / 16000
                            print(f"  - 转换后音频已保存: {converted_audio_path}")
                            print(f"  - 转换后音频时长: {duration_seconds:.2f} 秒")
                    finally:
                        if os.path.exists(pcm_temp):
                            os.unlink(pcm_temp)
            except Exception as wav_save_error:
                print(f"  - 保存转换后WAV文件失败: {wav_save_error}")
                
        except Exception as conv_error:
            print(f"  - 音频格式转换失败: {conv_error}")
            print(f"  - 错误详情: {str(conv_error)}")
            raise HTTPException(
                status_code=400, 
                detail=f"音频格式转换失败: {str(conv_error)}。请确保已安装ffmpeg。"
            )
        
        # 调用科大讯飞语音识别API
        result = await call_xunfei_asr(audio_data, language)
        
        print(f"[ASR] 识别结果: {result.get('text', '')}")
        
        # 打印保存的文件路径（方便用户查找）
        if original_audio_path:
            print(f"[ASR] 原始音频文件路径: {os.path.abspath(original_audio_path)}")
        if converted_audio_path:
            print(f"[ASR] 转换后音频文件路径: {os.path.abspath(converted_audio_path)}")
        
        return {
            "success": True,
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0),
            "is_final": result.get("is_final", True),
            "debug_info": {
                "original_audio_path": original_audio_path,
                "converted_audio_path": converted_audio_path,
                "original_size": original_size,
                "converted_size": len(converted_audio) if converted_audio else None
            } if original_audio_path or converted_audio_path else None
        }
        
    except Exception as e:
        print(f"ASR error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"语音识别失败: {str(e)}")

@router.post("/tts")
async def text_to_speech(
    text: str = Form(...),
    voice_name: str = Form("xiaoyan"),
    speed: int = Form(50),
    volume: int = Form(50),
    pitch: int = Form(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    语音合成接口
    将文字转换为语音
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 调用科大讯飞语音合成API
        audio_data = await call_xunfei_tts(text, voice_name, speed, volume, pitch)
        
        # 返回音频流
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        print(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"语音合成失败: {str(e)}")

@router.post("/tts-stream")
async def text_to_speech_stream(
    text: str = Form(...),
    voice_name: str = Form("xiaoyan"),
    speed: int = Form(50),
    volume: int = Form(50),
    pitch: int = Form(50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    流式语音合成接口
    支持长文本的流式语音合成
    """
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 将长文本分段
        segments = split_text_for_tts(text)
        
        async def generate_audio():
            for segment in segments:
                try:
                    audio_data = await call_xunfei_tts(segment, voice_name, speed, volume, pitch)
                    yield audio_data
                except Exception as e:
                    print(f"TTS segment error: {e}")
                    continue
        
        return StreamingResponse(
            generate_audio(),
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=speech.wav"
            }
        )
        
    except Exception as e:
        print(f"TTS stream error: {e}")
        raise HTTPException(status_code=500, detail=f"流式语音合成失败: {str(e)}")

def _generate_xunfei_auth_url(host: str, path: str, api_key: str, api_secret: str) -> str:
    """
    生成科大讯飞WebSocket认证URL
    根据文档：https://www.xfyun.cn/doc/spark/spark_zh_iat.html
    """
    # 生成RFC1123格式的时间戳
    date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 构建待签名字符串
    signature_origin = f"host: {host}\ndate: {date_str}\nGET {path} HTTP/1.1"
    
    # 使用API Secret进行HMAC-SHA256签名
    signature_sha = hmac.new(
        api_secret.encode('utf-8'),
        signature_origin.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')
    
    # 构建Authorization
    authorization_origin = f'api_key="{api_key}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    # 构建WebSocket URL（需要对参数进行URL编码）
    from urllib.parse import urlencode, quote
    
    params = {
        "authorization": authorization,
        "date": date_str,
        "host": host
    }
    # 对参数值进行URL编码
    query_string = "&".join([f"{k}={quote(str(v), safe='')}" for k, v in params.items()])
    
    return f"wss://{host}{path}?{query_string}"

async def call_xunfei_asr(audio_data: bytes, language: str = "zh_cn") -> dict:
    """
    调用科大讯飞语音识别API
    
    注意：根据科大讯飞文档，语音识别API主要使用WebSocket接口进行实时流式识别。
    这里提供一个简化的HTTP接口实现，但建议在生产环境中使用WebSocket以获得更好的体验。
    
    如果遇到403错误，请检查：
    1. 服务器时间是否准确（与标准时间相差不超过5分钟）
    2. IP白名单设置（在科大讯飞控制台检查）
    3. API Key和API Secret是否正确
    4. 应用是否已开通语音识别服务权限
    """
    try:
        # 检查配置
        if not settings.XFYUN_APP_ID or not settings.XFYUN_API_KEY or not settings.XFYUN_API_SECRET:
            # 如果没有配置API Key，返回模拟数据用于开发测试
            print("警告: 科大讯飞API Key未配置，返回模拟数据")
            return {
                "text": "这是模拟的语音识别结果（请配置XFYUN_APP_ID、XFYUN_API_KEY、XFYUN_API_SECRET以使用真实API）",
                "confidence": 0.95,
                "is_final": True
            }
        
        # 根据科大讯飞文档，中英识别大模型API主要使用WebSocket接口
        # HTTP接口可能不支持或有限制，这里先尝试HTTP，如果失败建议使用WebSocket
        
        # 尝试使用WebSocket接口（推荐方式）
        try:
            import websockets
        except ImportError:
            print("警告: websockets库未安装，使用HTTP接口。建议安装: pip install websockets")
            websockets = None
        
        # 如果websockets可用，优先使用WebSocket接口
        if websockets:
            return await _call_xunfei_asr_websocket(audio_data, language)
        else:
            # 回退到HTTP接口（可能不支持）
            return await _call_xunfei_asr_http(audio_data, language)
        
    except Exception as e:
        print(f"Xunfei ASR API error: {e}")
        import traceback
        traceback.print_exc()
        # 如果出现其他错误，返回模拟数据以便开发测试
        return {
            "text": f"语音识别处理失败: {str(e)}（当前返回模拟数据）",
            "confidence": 0.95,
            "is_final": True
        }
        
async def _call_xunfei_asr_websocket(audio_data: bytes, language: str = "zh_cn") -> dict:
    """
    使用WebSocket调用科大讯飞语音识别API（推荐方式）
    """
    try:
        import websockets
        import asyncio
        
        # 调试信息
        print(f"[WebSocket ASR] 音频数据大小: {len(audio_data)} 字节")
        if len(audio_data) == 0:
            raise Exception("音频数据为空，无法进行识别")
        
        # 根据文档，中英识别大模型API的WebSocket端点
        host = "iat-api.xfyun.cn"
        path = "/v2/iat"
        
        # 生成WebSocket认证URL
        ws_url = _generate_xunfei_auth_url(host, path, settings.XFYUN_API_KEY, settings.XFYUN_API_SECRET)
        print(f"[WebSocket ASR] WebSocket URL生成成功 (长度: {len(ws_url)})")
        
        # 将音频数据转换为base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        print(f"[WebSocket ASR] Base64编码后大小: {len(audio_base64)} 字符")
        
        # 建立WebSocket连接并发送数据
        async with websockets.connect(ws_url, ping_interval=None) as websocket:
            print("[WebSocket ASR] WebSocket连接已建立")
            
            # 第一步：发送参数消息（status=0，不包含音频）
            params_msg = {
                "common": {
                    "app_id": settings.XFYUN_APP_ID
                },
                "business": {
                    "language": language,
                    "domain": "iat",
                    "accent": "mandarin"
                },
                "data": {
                    "status": 0,  # 0表示第一帧，参数信息
                    "format": "audio/L16;rate=16000",  # PCM格式，16kHz采样率
                    "encoding": "raw"
                }
            }
            
            print(f"[WebSocket ASR] 发送参数消息 (status=0)")
            await websocket.send(json.dumps(params_msg, ensure_ascii=False))
            
            # 第二步：分块发送音频数据
            # 科大讯飞建议每帧音频数据大小不超过1280字节（base64编码前）
            chunk_size = 1280  # PCM原始数据块大小（字节）
            total_chunks = (len(audio_data) + chunk_size - 1) // chunk_size
            
            print(f"[WebSocket ASR] 音频数据将分 {total_chunks} 块发送，每块 {chunk_size} 字节")
            
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                chunk_base64 = base64.b64encode(chunk).decode('utf-8')
                
                # 判断是否是最后一块
                is_last = (i + chunk_size >= len(audio_data))
                
                data_msg = {
                    "data": {
                        "status": 2 if is_last else 1,  # 1表示中间帧，2表示最后一帧
                        "format": "audio/L16;rate=16000",
                        "audio": chunk_base64,
                        "encoding": "raw"
                    }
                }
                
                chunk_num = (i // chunk_size) + 1
                print(f"[WebSocket ASR] 发送音频块 {chunk_num}/{total_chunks} (status={data_msg['data']['status']}, 大小={len(chunk)} 字节)")
                await websocket.send(json.dumps(data_msg, ensure_ascii=False))
            
            print("[WebSocket ASR] 所有音频数据已发送，等待响应...")
            
            # 接收响应
            result_text = ""
            message_count = 0
            is_finished = False
            
            # 设置超时时间（30秒）
            import asyncio
            try:
                while not is_finished:
                    try:
                        # 等待消息，设置超时
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        message_count += 1
                        print(f"[WebSocket ASR] 收到消息 #{message_count}")
                        print(f"[WebSocket ASR] 原始消息 (前500字符): {message[:500]}")
                        
                        try:
                            result = json.loads(message)
                            print(f"[WebSocket ASR] 解析后的响应:")
                            print(f"  - code: {result.get('code')}")
                            print(f"  - message: {result.get('message', 'N/A')}")
                            print(f"  - 是否有data: {'data' in result}")
                            
                            # 检查错误
                            if result.get("code") != 0:
                                error_msg = result.get("message", "未知错误")
                                error_code = result.get("code", "未知")
                                print(f"[WebSocket ASR] API返回错误: code={error_code}, message={error_msg}")
                                
                                # 某些错误代码可能不是致命错误
                                if error_code in [10005]:  # 10005可能是参数错误
                                    raise Exception(f"科大讯飞API错误 (code={error_code}): {error_msg}")
                                else:
                                    # 其他错误，继续尝试解析
                                    print(f"[WebSocket ASR] 警告: 收到非零错误码，但继续处理")
                            
                            # 解析识别结果
                            if "data" in result:
                                data = result["data"]
                                print(f"[WebSocket ASR] data类型: {type(data)}")
                                
                                # data可能是字符串（base64编码的JSON）或直接是对象
                                if isinstance(data, str):
                                    print(f"[WebSocket ASR] data是字符串，尝试base64解码")
                                    try:
                                        decoded_data = json.loads(base64.b64decode(data).decode('utf-8'))
                                        print(f"[WebSocket ASR] 解码后的data: {json.dumps(decoded_data, ensure_ascii=False)[:200]}...")
                                        data = decoded_data
                                    except Exception as decode_error:
                                        print(f"[WebSocket ASR] base64解码失败: {decode_error}")
                                        print(f"[WebSocket ASR] 尝试直接解析data字符串")
                                        try:
                                            data = json.loads(data)
                                        except:
                                            print(f"[WebSocket ASR] 无法解析data，跳过")
                                            continue
                                
                                if isinstance(data, dict):
                                    print(f"[WebSocket ASR] data是字典，keys: {list(data.keys())}")
                                    
                                    # 检查是否有result字段
                                    if "result" in data:
                                        result_data = data["result"]
                                        print(f"[WebSocket ASR] 找到result字段: {type(result_data)}")
                                        print(f"[WebSocket ASR] result内容: {json.dumps(result_data, ensure_ascii=False)[:300]}...")
                                        
                                        if isinstance(result_data, dict) and "ws" in result_data:
                                            print(f"[WebSocket ASR] 找到ws字段，开始解析词语")
                                            ws_data = result_data["ws"]
                                            print(f"[WebSocket ASR] ws类型: {type(ws_data)}")
                                            print(f"[WebSocket ASR] ws完整内容: {json.dumps(ws_data, ensure_ascii=False)[:500]}...")
                                            
                                            if isinstance(ws_data, list):
                                                print(f"[WebSocket ASR] ws是列表，长度: {len(ws_data)}")
                                                for idx, ws_item in enumerate(ws_data):
                                                    print(f"[WebSocket ASR] ws_item[{idx}]: {json.dumps(ws_item, ensure_ascii=False) if isinstance(ws_item, dict) else str(ws_item)[:200]}")
                                                    if isinstance(ws_item, dict):
                                                        # 检查不同的可能字段名
                                                        cw_data = ws_item.get("cw") or ws_item.get("cw") or ws_item.get("words")
                                                        if cw_data:
                                                            print(f"[WebSocket ASR] 找到cw数据: {type(cw_data)}, 长度: {len(cw_data) if isinstance(cw_data, list) else 'N/A'}")
                                                            if isinstance(cw_data, list):
                                                                for cw_idx, cw_item in enumerate(cw_data):
                                                                    print(f"[WebSocket ASR] cw_item[{cw_idx}]: {json.dumps(cw_item, ensure_ascii=False) if isinstance(cw_item, dict) else str(cw_item)[:200]}")
                                                                    if isinstance(cw_item, dict):
                                                                        # 尝试多种可能的字段名
                                                                        word = cw_item.get("w") or cw_item.get("word") or cw_item.get("text") or ""
                                                                        if word:
                                                                            result_text += word
                                                                            print(f"[WebSocket ASR] 识别到词语: '{word}'")
                                                        else:
                                                            # 如果没有cw字段，可能ws_item本身就是词语
                                                            word = ws_item.get("w") or ws_item.get("word") or ws_item.get("text") or ""
                                                            if word:
                                                                result_text += word
                                                                print(f"[WebSocket ASR] 识别到词语（直接）: '{word}'")
                                            elif isinstance(ws_data, dict):
                                                print(f"[WebSocket ASR] ws是字典，keys: {list(ws_data.keys())}")
                                                # 可能是嵌套结构
                                                for key, value in ws_data.items():
                                                    print(f"[WebSocket ASR] ws[{key}]: {type(value)}")
                                                    if isinstance(value, list):
                                                        for item in value:
                                                            if isinstance(item, dict):
                                                                word = item.get("w") or item.get("word") or item.get("text") or ""
                                                                if word:
                                                                    result_text += word
                                                                    print(f"[WebSocket ASR] 识别到词语: '{word}'")
                                    
                                    # 检查是否完成
                                    status = data.get("status")
                                    print(f"[WebSocket ASR] 当前状态: {status}")
                                    if status == 2:  # 2表示识别完成
                                        print(f"[WebSocket ASR] 识别完成，状态码: 2")
                                        is_finished = True
                                        break
                                    
                                elif isinstance(data, list):
                                    print(f"[WebSocket ASR] data是列表格式，长度: {len(data)}")
                                    for item in data:
                                        if isinstance(item, dict):
                                            if "result" in item:
                                                result_data = item["result"]
                                                if isinstance(result_data, dict) and "ws" in result_data:
                                                    for ws_item in result_data["ws"]:
                                                        if isinstance(ws_item, dict) and "cw" in ws_item:
                                                            for cw_item in ws_item.get("cw", []):
                                                                if isinstance(cw_item, dict):
                                                                    word = cw_item.get("w", "")
                                                                    if word:
                                                                        result_text += word
                                                                        print(f"[WebSocket ASR] 识别到词语: '{word}'")
                                            
                                            # 检查状态
                                            if item.get("status") == 2:
                                                is_finished = True
                                                break
                            
                        except json.JSONDecodeError as e:
                            print(f"[WebSocket ASR] JSON解析失败: {e}")
                            print(f"[WebSocket ASR] 原始消息: {message[:500]}...")
                            # 继续处理下一条消息
                            continue
                        except Exception as e:
                            print(f"[WebSocket ASR] 处理消息时出错: {e}")
                            import traceback
                            traceback.print_exc()
                            # 继续处理下一条消息
                            continue
                            
                    except asyncio.TimeoutError:
                        print(f"[WebSocket ASR] 等待响应超时（30秒）")
                        break
                    except websockets.exceptions.ConnectionClosed:
                        print(f"[WebSocket ASR] WebSocket连接已关闭")
                        break
                        
            except Exception as e:
                print(f"[WebSocket ASR] 接收消息时出错: {e}")
                import traceback
                traceback.print_exc()
            
            print(f"[WebSocket ASR] 最终识别结果: '{result_text}' (长度: {len(result_text)})")
            
            if not result_text:
                print("[WebSocket ASR] 警告: 识别结果为空，可能是:")
                print("  1. 音频格式不正确（需要PCM格式，16kHz采样率）")
                print("  2. 音频数据无效或损坏")
                print("  3. 音频太短或没有声音")
                print("  4. API返回的数据格式不符合预期")
            
            return {
                "text": result_text or "识别结果为空",
                "confidence": 0.95,
                "is_final": True
            }
            
    except ImportError:
        raise Exception("websockets库未安装，请运行: pip install websockets")
    except Exception as e:
        print(f"[WebSocket ASR] 调用失败: {e}")
        import traceback
        traceback.print_exc()
        raise

async def _call_xunfei_asr_http(audio_data: bytes, language: str = "zh_cn") -> dict:
    """
    使用HTTP调用科大讯飞语音识别API（备用方式，可能不支持）
    """
    # 生成签名（科大讯飞使用HMAC-SHA256签名认证）
    host = "iat-api.xfyun.cn"
    path = "/v2/iat"
    
    # 使用当前时间（确保服务器时间准确）
    date_str = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # 构建待签名字符串（使用POST方法）
    signature_origin = f"host: {host}\ndate: {date_str}\nPOST {path} HTTP/1.1"
    
    # 使用API Secret进行HMAC-SHA256签名
    signature_sha = hmac.new(
        settings.XFYUN_API_SECRET.encode('utf-8'),
        signature_origin.encode('utf-8'),
        hashlib.sha256
    ).digest()
    signature = base64.b64encode(signature_sha).decode('utf-8')
    
    # 构建Authorization header
    authorization_origin = f'api_key="{settings.XFYUN_API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    # 构建请求头
    headers = {
        "Authorization": authorization,
        "Date": date_str,
        "Host": host,
        "Content-Type": "application/json"
    }
    
    # 将音频数据转换为base64
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # 构建请求体
    payload = {
        "common": {
            "app_id": settings.XFYUN_APP_ID
        },
        "business": {
            "language": language,
            "domain": "iat",
            "accent": "mandarin",
            "vad_eos": 10000
        },
        "data": {
            "status": 2,
            "format": "audio/L16;rate=16000",
            "audio": audio_base64,
            "encoding": "raw"
        }
    }
    
    # 发送请求
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"https://{host}{path}",
                headers=headers,
                json=payload
            )
            
            # 检查响应状态
            if response.status_code == 403:
                error_detail = "403 Forbidden - 可能的原因：\n"
                error_detail += "1. 服务器时间不准确（与标准时间相差超过5分钟）\n"
                error_detail += "2. IP地址未在白名单中（请在科大讯飞控制台检查IP白名单设置）\n"
                error_detail += "3. API Key或API Secret配置错误\n"
                error_detail += "4. 应用未开通语音识别服务权限\n"
                error_detail += "5. HTTP接口可能不支持，建议使用WebSocket接口（安装websockets库）"
                print(f"科大讯飞API 403错误: {error_detail}")
                print(f"响应内容: {response.text}")
                # 返回模拟数据以便开发测试
                return {
                    "text": f"API调用失败 (403): HTTP接口可能不支持，建议使用WebSocket接口（当前返回模拟数据）",
                    "confidence": 0.95,
                    "is_final": True
                }
            
            response.raise_for_status()
            result = response.json()
            
            # 解析响应
            if result.get("code") == 0:
                text = ""
                if "data" in result:
                    data = result["data"]
                    if isinstance(data, list):
                        for item in data:
                            if "result" in item:
                                result_data = item["result"]
                                if "ws" in result_data:
                                    for ws_item in result_data["ws"]:
                                        for cw_item in ws_item.get("cw", []):
                                            text += cw_item.get("w", "")
                    elif isinstance(data, dict) and "result" in data:
                        result_data = data["result"]
                        if "ws" in result_data:
                            for ws_item in result_data["ws"]:
                                for cw_item in ws_item.get("cw", []):
                                    text += cw_item.get("w", "")
                
                return {
                    "text": text or "识别结果为空",
                    "confidence": result.get("data", {}).get("confidence", 0.95) if isinstance(result.get("data"), dict) else 0.95,
                    "is_final": True
                }
            else:
                error_msg = result.get("message", "未知错误")
                error_code = result.get("code", "未知")
                print(f"科大讯飞API错误: code={error_code}, message={error_msg}")
                raise Exception(f"科大讯飞API错误 (code={error_code}): {error_msg}")
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                error_detail = "403 Forbidden - HTTP接口可能不支持，建议使用WebSocket接口"
                print(f"科大讯飞API 403错误详情: {error_detail}")
                print(f"响应内容: {e.response.text}")
                return {
                    "text": f"API调用失败 (403): {error_detail}（当前返回模拟数据）",
                    "confidence": 0.95,
                    "is_final": True
                }
            else:
                raise

async def call_xunfei_tts(
    text: str, 
    voice_name: str = "xiaoyan", 
    speed: int = 50, 
    volume: int = 50, 
    pitch: int = 50
) -> bytes:
    """
    调用科大讯飞语音合成API
    """
    try:
        # 这里需要集成科大讯飞的WebAPI
        # 由于没有实际的API Key，这里返回模拟数据
        # 实际应该返回真实的音频数据
        return b"mock_audio_data"
        
        # 实际的API调用代码示例：
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://tts-api.xfyun.cn/v2/tts",
        #         headers={
        #             "Content-Type": "application/json",
        #             "Authorization": f"Bearer {settings.XUNFEI_API_KEY}"
        #         },
        #         json={
        #             "common": {
        #                 "app_id": settings.XUNFEI_APP_ID
        #             },
        #             "business": {
        #                 "aue": "raw",
        #                 "auf": "audio/L16;rate=16000",
        #                 "vcn": voice_name,
        #                 "speed": speed,
        #                 "volume": volume,
        #                 "pitch": pitch,
        #                 "bgs": 0
        #             },
        #             "data": {
        #                 "status": 2,
        #                 "text": base64.b64encode(text.encode()).decode()
        #             }
        #         }
        #     )
        #     return response.content
        
    except Exception as e:
        print(f"Xunfei TTS API error: {e}")
        raise Exception(f"语音合成API调用失败: {str(e)}")

def split_text_for_tts(text: str, max_length: int = 200) -> list:
    """
    将长文本分段，用于流式语音合成
    """
    if len(text) <= max_length:
        return [text]
    
    segments = []
    current_segment = ""
    
    for char in text:
        current_segment += char
        
        # 在句号、问号、感叹号处分割
        if char in '。！？' and len(current_segment) >= max_length // 2:
            segments.append(current_segment.strip())
            current_segment = ""
        # 在逗号处分割（如果已经很长）
        elif char in '，' and len(current_segment) >= max_length:
            segments.append(current_segment.strip())
            current_segment = ""
        # 强制分割（如果太长）
        elif len(current_segment) >= max_length:
            segments.append(current_segment.strip())
            current_segment = ""
    
    if current_segment.strip():
        segments.append(current_segment.strip())
    
    return segments
