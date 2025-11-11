"""
行程管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.trip import Trip as TripModel, Itinerary as ItineraryModel, ItineraryItem as ItineraryItemModel, Expense as ExpenseModel
from app.schemas.trip import (
    TripCreate, TripUpdate, Trip, TripListResponse,
    ItineraryCreate, ItineraryUpdate, Itinerary,
    ItineraryItemCreate, ItineraryItemUpdate, ItineraryItem,
    ExpenseCreate, ExpenseUpdate, Expense, ExpenseListResponse,
    TripStats, ExpenseStats
)

router = APIRouter()

# 行程管理
@router.post("/", response_model=Trip)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新行程"""
    try:
        # 自动计算行程天数
        duration_days = trip_data.duration_days if trip_data.duration_days else 1
        if trip_data.start_date and trip_data.end_date:
            # 计算天数：结束日期 - 开始日期 + 1
            # 例如：2025-11-11 到 2025-11-11 是 1 天
            # 例如：2025-11-11 到 2025-11-13 是 3 天
            try:
                start_date = trip_data.start_date
                end_date = trip_data.end_date
                
                # 转换为date对象
                if isinstance(start_date, datetime):
                    start_day = start_date.date()
                elif hasattr(start_date, 'date'):
                    start_day = start_date.date()
                else:
                    start_day = start_date
                    
                if isinstance(end_date, datetime):
                    end_day = end_date.date()
                elif hasattr(end_date, 'date'):
                    end_day = end_date.date()
                else:
                    end_day = end_date
                
                # 计算天数差
                if hasattr(start_day, '__sub__') and hasattr(end_day, '__sub__'):
                    duration_days = (end_day - start_day).days + 1
                    duration_days = max(1, duration_days)  # 至少1天
            except Exception as e:
                print(f"计算行程天数时出错: {e}, 使用默认值1")
                import traceback
                traceback.print_exc()
                duration_days = 1
        
        # 创建行程
        trip = TripModel(
            user_id=current_user.id,
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            duration_days=duration_days,  # 使用自动计算的天数
            budget_total=trip_data.budget_total,
            currency=trip_data.currency,
            status=trip_data.status,
            is_public=trip_data.is_public,
            tags=trip_data.tags or [],
            preferences=trip_data.preferences or {},
            traveler_count=trip_data.traveler_count
        )
        
        db.add(trip)
        db.flush()  # 获取trip.id
        
        # 创建行程安排
        if trip_data.itineraries:
            for itinerary_data in trip_data.itineraries:
                itinerary = ItineraryModel(
                    trip_id=trip.id,
                    day_number=itinerary_data.day_number,
                    date=itinerary_data.date,
                    title=itinerary_data.title,
                    description=itinerary_data.description
                )
                
                db.add(itinerary)
                db.flush()  # 获取itinerary.id
                
                # 创建行程项目
                if itinerary_data.items:
                    for item_data in itinerary_data.items:
                        item = ItineraryItemModel(
                            itinerary_id=itinerary.id,
                            poi_id=item_data.poi_id,
                            name=item_data.name,
                            description=item_data.description,
                            address=item_data.address,
                            coordinates=item_data.coordinates.model_dump() if item_data.coordinates else None,
                            category=item_data.category,
                            start_time=item_data.start_time,
                            end_time=item_data.end_time,
                            estimated_duration=item_data.estimated_duration,
                            estimated_cost=item_data.estimated_cost,
                            rating=item_data.rating,
                            price_level=item_data.price_level,
                            phone=item_data.phone,
                            website=item_data.website,
                            opening_hours=item_data.opening_hours,
                            images=item_data.images or [],
                            order_index=item_data.order_index,
                            is_completed=item_data.is_completed,
                            notes=item_data.notes
                        )
                        db.add(item)
        
        db.commit()
        db.refresh(trip)
        return trip
        
    except Exception as e:
        db.rollback()
        print(f"Create trip error: {e}")
        raise HTTPException(status_code=500, detail=f"创建行程失败: {str(e)}")

@router.get("/", response_model=TripListResponse)
async def get_trips(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="行程状态"),
    destination: Optional[str] = Query(None, description="目的地"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程列表"""
    try:
        query = db.query(TripModel).filter(TripModel.user_id == current_user.id)
        
        # 筛选条件
        if status:
            query = query.filter(TripModel.status == status)
        if destination:
            query = query.filter(TripModel.destination.ilike(f"%{destination}%"))
        
        # 排序
        if sort_order == "desc":
            query = query.order_by(desc(getattr(TripModel, sort_by)))
        else:
            query = query.order_by(asc(getattr(TripModel, sort_by)))
        
        # 分页
        total = query.count()
        trips = query.offset((page - 1) * size).limit(size).all()
        
        return TripListResponse(
            trips=trips,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total
        )
        
    except Exception as e:
        print(f"Get trips error: {e}")
        raise HTTPException(status_code=500, detail=f"获取行程列表失败: {str(e)}")

@router.get("/{trip_id}", response_model=Trip)
async def get_trip(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程详情"""
    try:
        from sqlalchemy.orm import joinedload
        
        # 使用joinedload预加载关联数据
        trip = db.query(TripModel).options(
            joinedload(TripModel.itineraries).joinedload(ItineraryModel.items),
            joinedload(TripModel.expenses)
        ).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get trip error: {e}")
        raise HTTPException(status_code=500, detail=f"获取行程详情失败: {str(e)}")

@router.put("/{trip_id}", response_model=Trip)
async def update_trip(
    trip_id: str = Path(..., description="行程ID"),
    trip_data: TripUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新行程"""
    try:
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 更新字段
        update_data = trip_data.model_dump(exclude_unset=True)
        
        # 如果更新了开始日期或结束日期，自动重新计算行程天数
        if 'start_date' in update_data or 'end_date' in update_data:
            start_date = update_data.get('start_date', trip.start_date)
            end_date = update_data.get('end_date', trip.end_date)
            if start_date and end_date:
                try:
                    # 转换为date对象
                    if isinstance(start_date, datetime):
                        start_day = start_date.date()
                    elif hasattr(start_date, 'date'):
                        start_day = start_date.date()
                    else:
                        start_day = start_date
                        
                    if isinstance(end_date, datetime):
                        end_day = end_date.date()
                    elif hasattr(end_date, 'date'):
                        end_day = end_date.date()
                    else:
                        end_day = end_date
                    
                    # 计算天数差
                    if hasattr(start_day, '__sub__') and hasattr(end_day, '__sub__'):
                        duration_days = (end_day - start_day).days + 1
                        update_data['duration_days'] = max(1, duration_days)  # 至少1天
                except Exception as e:
                    print(f"更新行程天数时出错: {e}")
                    # 不更新duration_days，保持原值
        
        for field, value in update_data.items():
            setattr(trip, field, value)
        
        trip.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(trip)
        
        return trip
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Update trip error: {e}")
        raise HTTPException(status_code=500, detail=f"更新行程失败: {str(e)}")

@router.delete("/{trip_id}")
async def delete_trip(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除行程"""
    try:
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        db.delete(trip)
        db.commit()
        
        return {"message": "行程删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Delete trip error: {e}")
        raise HTTPException(status_code=500, detail=f"删除行程失败: {str(e)}")

# 行程安排管理
@router.post("/{trip_id}/itineraries", response_model=Itinerary)
async def create_itinerary(
    trip_id: str = Path(..., description="行程ID"),
    itinerary_data: ItineraryCreate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建行程安排"""
    try:
        # 检查行程是否存在
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 创建行程安排
        itinerary = ItineraryModel(
            trip_id=trip_id,
            day_number=itinerary_data.day_number,
            date=itinerary_data.date,
            title=itinerary_data.title,
            description=itinerary_data.description
        )
        
        db.add(itinerary)
        db.flush()
        
        # 创建行程项目（节点）
        if itinerary_data.items:
            for item_data in itinerary_data.items:
                item = ItineraryItemModel(
                    itinerary_id=itinerary.id,
                    poi_id=item_data.poi_id,
                    name=item_data.name,
                    description=item_data.description,
                    address=item_data.address,
                    coordinates=item_data.coordinates.model_dump() if item_data.coordinates else None,
                    category=item_data.category,
                    start_time=item_data.start_time,
                    end_time=item_data.end_time,
                    estimated_duration=item_data.estimated_duration,
                    estimated_cost=item_data.estimated_cost,
                    rating=item_data.rating,
                    price_level=item_data.price_level,
                    phone=item_data.phone,
                    website=item_data.website,
                    opening_hours=item_data.opening_hours,
                    images=item_data.images or [],
                    order_index=item_data.order_index,
                    is_completed=item_data.is_completed,
                    notes=item_data.notes
                )
                db.add(item)
        
        db.commit()
        db.refresh(itinerary)
        return itinerary
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Create itinerary error: {e}")
        raise HTTPException(status_code=500, detail=f"创建行程安排失败: {str(e)}")

@router.get("/{trip_id}/itineraries", response_model=List[Itinerary])
async def get_itineraries(
    trip_id: str = Path(..., description="行程ID"),
    day_number: Optional[int] = Query(None, description="第几天"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程安排列表"""
    try:
        # 检查行程是否存在
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        query = db.query(ItineraryModel).filter(ItineraryModel.trip_id == trip_id)
        
        if day_number:
            query = query.filter(ItineraryModel.day_number == day_number)
        
        itineraries = query.order_by(ItineraryModel.day_number, ItineraryModel.start_time).all()
        return itineraries
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get itineraries error: {e}")
        raise HTTPException(status_code=500, detail=f"获取行程安排失败: {str(e)}")

# 费用管理
@router.post("/{trip_id}/expenses", response_model=Expense)
async def create_expense(
    trip_id: str = Path(..., description="行程ID"),
    expense_data: ExpenseCreate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建费用记录"""
    try:
        # 检查行程是否存在
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 创建费用记录
        expense = ExpenseModel(
            trip_id=trip_id,
            itinerary_id=expense_data.itinerary_id,
            amount=expense_data.amount,
            currency=expense_data.currency,
            category=expense_data.category,
            description=expense_data.description,
            location=expense_data.location,
            coordinates=expense_data.coordinates.dict() if expense_data.coordinates else None,
            payment_method=expense_data.payment_method,
            receipt_image=expense_data.receipt_image,
            is_shared=expense_data.is_shared,
            shared_amount=expense_data.shared_amount,
            notes=expense_data.notes,
            expense_date=expense_data.expense_date or datetime.utcnow()
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        return expense
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Create expense error: {e}")
        raise HTTPException(status_code=500, detail=f"创建费用记录失败: {str(e)}")

@router.get("/{trip_id}/expenses", response_model=ExpenseListResponse)
async def get_expenses(
    trip_id: str = Path(..., description="行程ID"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    category: Optional[str] = Query(None, description="费用类别"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取费用记录列表"""
    try:
        # 检查行程是否存在
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        query = db.query(ExpenseModel).filter(ExpenseModel.trip_id == trip_id)
        
        # 筛选条件
        if category:
            query = query.filter(ExpenseModel.category == category)
        if start_date:
            query = query.filter(ExpenseModel.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseModel.expense_date <= end_date)
        
        # 计算总金额
        total_amount = query.with_entities(func.sum(ExpenseModel.amount)).scalar() or 0
        
        # 分页
        total = query.count()
        expenses = query.order_by(desc(ExpenseModel.expense_date)).offset((page - 1) * size).limit(size).all()
        
        return ExpenseListResponse(
            expenses=expenses,
            total=total,
            page=page,
            size=size,
            has_next=(page * size) < total,
            total_amount=float(total_amount)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get expenses error: {e}")
        raise HTTPException(status_code=500, detail=f"获取费用记录失败: {str(e)}")

# 统计接口
@router.get("/stats/overview", response_model=TripStats)
async def get_trip_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取行程统计概览"""
    try:
        # 基础统计
        total_trips = db.query(TripModel).filter(TripModel.user_id == current_user.id).count()
        active_trips = db.query(TripModel).filter(
            TripModel.user_id == current_user.id,
            TripModel.status == "active"
        ).count()
        completed_trips = db.query(TripModel).filter(
            TripModel.user_id == current_user.id,
            TripModel.status == "completed"
        ).count()
        
        # 总费用
        total_expenses = db.query(func.sum(ExpenseModel.amount)).join(TripModel).filter(
            TripModel.user_id == current_user.id
        ).scalar() or 0
        
        # 平均行程时长
        avg_duration = db.query(func.avg(TripModel.duration_days)).filter(
            TripModel.user_id == current_user.id
        ).scalar() or 0
        
        # 最常访问的目的地
        popular_destinations = db.query(
            TripModel.destination,
            func.count(TripModel.id).label('count')
        ).filter(
            TripModel.user_id == current_user.id,
            TripModel.destination.isnot(None)
        ).group_by(TripModel.destination).order_by(desc('count')).limit(5).all()
        
        return TripStats(
            total_trips=total_trips,
            active_trips=active_trips,
            completed_trips=completed_trips,
            total_expenses=float(total_expenses),
            average_trip_duration=float(avg_duration),
            most_visited_destinations=[
                {"destination": dest, "count": count} 
                for dest, count in popular_destinations
            ]
        )
        
    except Exception as e:
        print(f"Get trip stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取行程统计失败: {str(e)}")

@router.get("/{trip_id}/expenses/stats", response_model=ExpenseStats)
async def get_expense_stats(
    trip_id: str = Path(..., description="行程ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取费用统计"""
    try:
        # 检查行程是否存在
        trip = db.query(TripModel).filter(
            TripModel.id == trip_id,
            TripModel.user_id == current_user.id
        ).first()
        
        if not trip:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        # 总金额
        total_amount = db.query(func.sum(ExpenseModel.amount)).filter(
            ExpenseModel.trip_id == trip_id
        ).scalar() or 0
        
        # 分类统计
        category_stats = db.query(
            ExpenseModel.category,
            func.sum(ExpenseModel.amount).label('amount')
        ).filter(ExpenseModel.trip_id == trip_id).group_by(ExpenseModel.category).all()
        
        category_breakdown = {cat: float(amount) for cat, amount in category_stats}
        
        # 日平均费用
        expense_days = db.query(func.count(func.distinct(func.date(ExpenseModel.expense_date)))).filter(
            ExpenseModel.trip_id == trip_id
        ).scalar() or 1
        
        daily_average = float(total_amount) / expense_days
        
        return ExpenseStats(
            total_amount=float(total_amount),
            category_breakdown=category_breakdown,
            daily_average=daily_average,
            monthly_trend=[],  # 可以后续实现
            budget_vs_actual={}  # 可以后续实现
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Get expense stats error: {e}")
        raise HTTPException(status_code=500, detail=f"获取费用统计失败: {str(e)}")


# ==================== 行程节点管理 ====================

@router.post("/itineraries/{itinerary_id}/items", response_model=ItineraryItem)
async def create_itinerary_item(
    itinerary_id: str = Path(..., description="行程ID"),
    item_data: ItineraryItemCreate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加行程节点"""
    try:
        # 验证itinerary是否存在且属于当前用户
        from sqlalchemy.orm import joinedload
        
        itinerary = db.query(ItineraryModel).options(
            joinedload(ItineraryModel.trip)
        ).filter(
            ItineraryModel.id == itinerary_id
        ).first()
        
        if not itinerary:
            raise HTTPException(status_code=404, detail="行程不存在")
        
        if itinerary.trip.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限操作此行程")
        
        # 创建节点
        item = ItineraryItemModel(
            itinerary_id=itinerary_id,
            poi_id=item_data.poi_id,
            name=item_data.name,
            description=item_data.description,
            address=item_data.address,
            coordinates=item_data.coordinates.model_dump() if item_data.coordinates else None,
            category=item_data.category,
            start_time=item_data.start_time,
            end_time=item_data.end_time,
            estimated_duration=item_data.estimated_duration,
            estimated_cost=item_data.estimated_cost,
            rating=item_data.rating,
            price_level=item_data.price_level,
            phone=item_data.phone,
            website=item_data.website,
            opening_hours=item_data.opening_hours,
            images=item_data.images or [],
            order_index=item_data.order_index if item_data.order_index is not None else 0,
            is_completed=item_data.is_completed if item_data.is_completed is not None else False,
            notes=item_data.notes
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Create itinerary item error: {e}")
        raise HTTPException(status_code=500, detail=f"添加节点失败: {str(e)}")


@router.put("/itineraries/{itinerary_id}/items/{item_id}", response_model=ItineraryItem)
async def update_itinerary_item(
    itinerary_id: str = Path(..., description="行程ID"),
    item_id: str = Path(..., description="节点ID"),
    item_data: ItineraryItemUpdate = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新行程节点"""
    try:
        # 验证节点是否存在且有权限
        from sqlalchemy.orm import joinedload
        
        item = db.query(ItineraryItemModel).options(
            joinedload(ItineraryItemModel.itinerary).joinedload(ItineraryModel.trip)
        ).filter(
            ItineraryItemModel.id == item_id,
            ItineraryItemModel.itinerary_id == itinerary_id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        if item.itinerary.trip.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限操作此节点")
        
        # 更新字段
        update_data = item_data.model_dump(exclude_unset=True)
        
        # 处理coordinates
        if 'coordinates' in update_data and update_data['coordinates']:
            update_data['coordinates'] = update_data['coordinates']
        
        for field, value in update_data.items():
            setattr(item, field, value)
        
        db.commit()
        db.refresh(item)
        
        return item
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Update itinerary item error: {e}")
        raise HTTPException(status_code=500, detail=f"更新节点失败: {str(e)}")


@router.delete("/itineraries/{itinerary_id}/items/{item_id}")
async def delete_itinerary_item(
    itinerary_id: str = Path(..., description="行程ID"),
    item_id: str = Path(..., description="节点ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除行程节点"""
    try:
        # 验证节点是否存在且有权限
        from sqlalchemy.orm import joinedload
        
        item = db.query(ItineraryItemModel).options(
            joinedload(ItineraryItemModel.itinerary).joinedload(ItineraryModel.trip)
        ).filter(
            ItineraryItemModel.id == item_id,
            ItineraryItemModel.itinerary_id == itinerary_id
        ).first()
        
        if not item:
            raise HTTPException(status_code=404, detail="节点不存在")
        
        if item.itinerary.trip.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="无权限操作此节点")
        
        db.delete(item)
        db.commit()
        
        return {"message": "节点删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Delete itinerary item error: {e}")
        raise HTTPException(status_code=500, detail=f"删除节点失败: {str(e)}")


# AI行程规划助手
from pydantic import BaseModel, Field
from app.services.trip_planning_ai_service import TripPlanningAIService

class PlanningAIQueryRequest(BaseModel):
    """AI行程规划查询请求模型"""
    query: str = Field(..., description="用户查询")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="对话历史")

class PlanningAIQueryResponse(BaseModel):
    """AI行程规划查询响应模型"""
    response: str = Field(..., description="AI响应")
    action_performed: bool = Field(False, description="是否执行了操作")
    pending_action: Optional[Dict[str, Any]] = Field(None, description="待确认的操作（Function Call）")

class PlanningExecuteActionRequest(BaseModel):
    """执行操作请求模型"""
    function_name: str = Field(..., description="函数名称")
    arguments: str = Field(..., description="函数参数（JSON字符串）")

@router.post("/{trip_id}/planning/ai/query", response_model=PlanningAIQueryResponse)
async def planning_ai_query(
    trip_id: str = Path(..., description="行程ID"),
    request: PlanningAIQueryRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI行程规划查询"""
    service = TripPlanningAIService(db)
    
    try:
        result = await service.process_natural_language_query(
            query=request.query,
            user_id=current_user.id,
            trip_id=trip_id,
            conversation_history=request.conversation_history
        )
        
        return PlanningAIQueryResponse(
            response=result.get('content', ''),
            action_performed=False,
            pending_action=result.get('pending_action')
        )
    except Exception as e:
        import traceback
        print(f"AI行程规划查询异常: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI查询失败: {str(e)}")

@router.post("/{trip_id}/planning/ai/execute", response_model=Dict[str, Any])
async def planning_execute_ai_action(
    trip_id: str = Path(..., description="行程ID"),
    request: PlanningExecuteActionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行AI请求的操作（Function Call）"""
    service = TripPlanningAIService(db)
    
    try:
        import json
        arguments = json.loads(request.arguments)
        
        result = await service.execute_tool_call(
            function_name=request.function_name,
            arguments=arguments,
            user_id=current_user.id,
            trip_id=trip_id
        )
        
        return {
            "success": True,
            "message": result.get('message', '操作执行成功'),
            "data": result.get('data')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行操作失败: {str(e)}")

# AI创建行程助手
from app.services.trip_ai_service import TripAIService

class AIQueryRequest(BaseModel):
    """AI查询请求模型"""
    query: str = Field(..., description="用户查询")
    conversation_history: Optional[List[Dict[str, Any]]] = Field(None, description="对话历史")

class AIQueryResponse(BaseModel):
    """AI查询响应模型"""
    response: str = Field(..., description="AI响应")
    action_performed: bool = Field(False, description="是否执行了操作")
    pending_action: Optional[Dict[str, Any]] = Field(None, description="待确认的操作（Function Call）")

class ExecuteActionRequest(BaseModel):
    """执行操作请求模型"""
    function_name: str = Field(..., description="函数名称")
    arguments: str = Field(..., description="函数参数（JSON字符串）")

@router.post("/ai/query", response_model=AIQueryResponse)
async def ai_query(
    request: AIQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI创建行程查询"""
    service = TripAIService(db)
    
    try:
        result = await service.process_natural_language_query(
            query=request.query,
            user_id=current_user.id,
            conversation_history=request.conversation_history
        )
        
        return AIQueryResponse(
            response=result.get('content', ''),
            action_performed=False,
            pending_action=result.get('pending_action')
        )
    except Exception as e:
        import traceback
        print(f"AI查询异常: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"AI查询失败: {str(e)}")

@router.post("/ai/execute", response_model=Dict[str, Any])
async def execute_ai_action(
    request: ExecuteActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """执行AI请求的操作（Function Call）"""
    service = TripAIService(db)
    
    try:
        import json
        arguments = json.loads(request.arguments)
        
        result = await service.execute_tool_call(
            function_name=request.function_name,
            arguments=arguments,
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "message": result.get('message', '操作执行成功'),
            "data": result.get('data')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行操作失败: {str(e)}")
