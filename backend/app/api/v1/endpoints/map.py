"""
地图API端点
提供POI搜索、地理编码、路线规划等地图服务
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.utils.baidu_map_tools import baidu_map_tools

router = APIRouter()


# 请求/响应模型
class POISearchRequest(BaseModel):
    """POI搜索请求"""
    keyword: str = Field(..., description="搜索关键词")
    city: str = Field(..., description="城市名称")
    category: str = Field("attraction", description="POI类别")


class RouteRequest(BaseModel):
    """路线计算请求"""
    origin: Dict[str, float] = Field(..., description="起点坐标 {lat, lng}")
    destination: Dict[str, float] = Field(..., description="终点坐标 {lat, lng}")
    mode: str = Field("driving", description="交通方式：driving/walking/transit/bicycling")


class GeocodeRequest(BaseModel):
    """地理编码请求"""
    address: str = Field(..., description="地址")
    city: str = Field(None, description="城市（可选）")


@router.post("/poi/search")
async def search_poi(
    request: POISearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索POI"""
    try:
        result = baidu_map_tools.search_poi(
            keyword=request.keyword,
            city=request.city,
            category=request.category
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POI搜索失败: {str(e)}")


@router.post("/route")
async def calculate_route(
    request: RouteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """计算路线"""
    try:
        result = baidu_map_tools.calculate_route(
            origin=request.origin,
            destination=request.destination,
            mode=request.mode
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"路线计算失败: {str(e)}")


@router.post("/geocode")
async def geocode_address(
    request: GeocodeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """地理编码 - 地址转坐标"""
    try:
        address = f"{request.city or ''}{request.address}"
        result = baidu_map_tools.geocode(address)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地理编码失败: {str(e)}")


@router.get("/health")
async def map_health():
    """地图服务健康检查"""
    return {
        "status": "healthy",
        "service": "map",
        "version": "1.0.0"
    }

