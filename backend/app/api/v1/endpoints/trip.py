"""
行程管理API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.trip import Trip as TripModel, Itinerary as ItineraryModel, ItineraryItem as ItineraryItemModel, Expense as ExpenseModel, Budget as BudgetModel
from app.schemas.trip import (
    TripCreate, TripUpdate, Trip, TripListResponse,
    ItineraryCreate, ItineraryUpdate, Itinerary,
    ItineraryItemCreate, ItineraryItemUpdate, ItineraryItem,
    ExpenseCreate, ExpenseUpdate, Expense, ExpenseListResponse,
    BudgetCreate, BudgetUpdate, Budget,
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
        # 创建行程
        trip = TripModel(
            user_id=current_user.id,
            title=trip_data.title,
            description=trip_data.description,
            destination=trip_data.destination,
            start_date=trip_data.start_date,
            end_date=trip_data.end_date,
            duration_days=trip_data.duration_days,
            budget=trip_data.budget,
            status=trip_data.status,
            is_public=trip_data.is_public,
            tags=trip_data.tags or []
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
                    description=itinerary_data.description,
                    start_time=itinerary_data.start_time,
                    end_time=itinerary_data.end_time,
                    location=itinerary_data.location,
                    coordinates=itinerary_data.coordinates.dict() if itinerary_data.coordinates else None,
                    category=itinerary_data.category,
                    priority=itinerary_data.priority,
                    estimated_duration=itinerary_data.estimated_duration,
                    estimated_cost=itinerary_data.estimated_cost,
                    notes=itinerary_data.notes,
                    is_completed=itinerary_data.is_completed
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
                            coordinates=item_data.coordinates.dict() if item_data.coordinates else None,
                            category=item_data.category,
                            rating=item_data.rating,
                            price_level=item_data.price_level,
                            phone=item_data.phone,
                            website=item_data.website,
                            opening_hours=item_data.opening_hours,
                            images=item_data.images or [],
                            order_index=item_data.order_index,
                            is_visited=item_data.is_visited,
                            visit_notes=item_data.visit_notes
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
        trip = db.query(TripModel).filter(
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
        update_data = trip_data.dict(exclude_unset=True)
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
            description=itinerary_data.description,
            start_time=itinerary_data.start_time,
            end_time=itinerary_data.end_time,
            location=itinerary_data.location,
            coordinates=itinerary_data.coordinates.dict() if itinerary_data.coordinates else None,
            category=itinerary_data.category,
            priority=itinerary_data.priority,
            estimated_duration=itinerary_data.estimated_duration,
            estimated_cost=itinerary_data.estimated_cost,
            notes=itinerary_data.notes,
            is_completed=itinerary_data.is_completed
        )
        
        db.add(itinerary)
        db.flush()
        
        # 创建行程项目
        if itinerary_data.items:
            for item_data in itinerary_data.items:
                item = ItineraryItemModel(
                    itinerary_id=itinerary.id,
                    poi_id=item_data.poi_id,
                    name=item_data.name,
                    description=item_data.description,
                    address=item_data.address,
                    coordinates=item_data.coordinates.dict() if item_data.coordinates else None,
                    category=item_data.category,
                    rating=item_data.rating,
                    price_level=item_data.price_level,
                    phone=item_data.phone,
                    website=item_data.website,
                    opening_hours=item_data.opening_hours,
                    images=item_data.images or [],
                    order_index=item_data.order_index,
                    is_visited=item_data.is_visited,
                    visit_notes=item_data.visit_notes
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
