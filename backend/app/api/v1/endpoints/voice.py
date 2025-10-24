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
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.core.config import settings

router = APIRouter()

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
        
        # 调用科大讯飞语音识别API
        result = await call_xunfei_asr(audio_data, language)
        
        return {
            "success": True,
            "text": result.get("text", ""),
            "confidence": result.get("confidence", 0),
            "is_final": result.get("is_final", True)
        }
        
    except Exception as e:
        print(f"ASR error: {e}")
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

async def call_xunfei_asr(audio_data: bytes, language: str = "zh_cn") -> dict:
    """
    调用科大讯飞语音识别API
    """
    try:
        # 这里需要集成科大讯飞的WebAPI
        # 由于没有实际的API Key，这里返回模拟数据
        return {
            "text": "这是模拟的语音识别结果",
            "confidence": 0.95,
            "is_final": True
        }
        
        # 实际的API调用代码示例：
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         "https://iat-api.xfyun.cn/v2/iat",
        #         headers={
        #             "Content-Type": "application/json",
        #             "Authorization": f"Bearer {settings.XUNFEI_API_KEY}"
        #         },
        #         json={
        #             "common": {
        #                 "app_id": settings.XUNFEI_APP_ID
        #             },
        #             "business": {
        #                 "language": language,
        #                 "domain": "iat",
        #                 "accent": "mandarin"
        #             },
        #             "data": {
        #                 "status": 2,
        #                 "format": "audio/L16;rate=16000",
        #                 "audio": base64.b64encode(audio_data).decode(),
        #                 "encoding": "raw"
        #             }
        #         }
        #     )
        #     return response.json()
        
    except Exception as e:
        print(f"Xunfei ASR API error: {e}")
        raise Exception(f"语音识别API调用失败: {str(e)}")

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
