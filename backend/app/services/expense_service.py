"""
费用管理服务
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid

from ..models.trip import Expense, Trip
from ..schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummary, CategoryStats


class ExpenseService:
    """费用管理服务"""
    
    def __init__(self, db: Session):
        self.db = db

    async def get_expenses(
        self,
        user_id: str,
        trip_id: Optional[str] = None,
        category: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ExpenseResponse]:
        """获取费用列表"""
        query = self.db.query(Expense).join(Trip).filter(Trip.user_id == user_id)
        
        if trip_id:
            query = query.filter(Expense.trip_id == trip_id)
        if category:
            query = query.filter(Expense.category == category)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        expenses = query.offset(skip).limit(limit).all()
        return [ExpenseResponse.from_orm(expense) for expense in expenses]

    async def get_expense(self, expense_id: str, user_id: str) -> Optional[ExpenseResponse]:
        """获取单个费用"""
        expense = self.db.query(Expense).join(Trip).filter(
            Expense.id == expense_id,
            Trip.user_id == user_id
        ).first()
        
        if expense:
            return ExpenseResponse.from_orm(expense)
        return None

    async def create_expense(self, expense_data: ExpenseCreate, user_id: str) -> ExpenseResponse:
        """创建费用记录"""
        # 验证行程是否属于用户
        trip = self.db.query(Trip).filter(
            Trip.id == expense_data.trip_id,
            Trip.user_id == user_id
        ).first()
        
        if not trip:
            raise ValueError("行程不存在")
        
        expense = Expense(
            id=str(uuid.uuid4()),
            trip_id=expense_data.trip_id,
            category=expense_data.category,
            amount=expense_data.amount,
            description=expense_data.description,
            expense_date=expense_data.expense_date,
            location=expense_data.location,
            currency=expense_data.currency
        )
        
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        
        # 更新预算
        await self._update_budget(expense_data.trip_id)
        
        return ExpenseResponse.from_orm(expense)

    async def update_expense(
        self, 
        expense_id: str, 
        expense_data: ExpenseUpdate, 
        user_id: str
    ) -> Optional[ExpenseResponse]:
        """更新费用记录"""
        expense = self.db.query(Expense).join(Trip).filter(
            Expense.id == expense_id,
            Trip.user_id == user_id
        ).first()
        
        if not expense:
            return None
        
        update_data = expense_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        self.db.commit()
        self.db.refresh(expense)
        
        # 更新预算
        await self._update_budget(expense.trip_id)
        
        return ExpenseResponse.from_orm(expense)

    async def delete_expense(self, expense_id: str, user_id: str) -> bool:
        """删除费用记录"""
        expense = self.db.query(Expense).join(Trip).filter(
            Expense.id == expense_id,
            Trip.user_id == user_id
        ).first()
        
        if not expense:
            return False
        
        trip_id = expense.trip_id
        self.db.delete(expense)
        self.db.commit()
        
        # 更新预算
        await self._update_budget(trip_id)
        
        return True

    async def get_expense_summary(
        self,
        user_id: str,
        trip_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ExpenseSummary:
        """获取费用统计摘要"""
        query = self.db.query(Expense).join(Trip).filter(Trip.user_id == user_id)
        
        if trip_id:
            query = query.filter(Expense.trip_id == trip_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        # 总金额和笔数
        total_result = query.with_entities(
            func.sum(Expense.amount).label('total_amount'),
            func.count(Expense.id).label('total_count')
        ).first()
        
        total_amount = total_result.total_amount or 0
        total_count = total_result.total_count or 0
        average_amount = total_amount / total_count if total_count > 0 else 0
        
        # 分类明细
        category_results = query.with_entities(
            Expense.category,
            func.sum(Expense.amount).label('amount'),
            func.count(Expense.id).label('count')
        ).group_by(Expense.category).all()
        
        category_breakdown = {}
        for result in category_results:
            percentage = (result.amount / total_amount * 100) if total_amount > 0 else 0
            category_breakdown[result.category] = {
                'amount': result.amount,
                'count': result.count,
                'percentage': round(percentage, 2)
            }
        
        # 每日明细
        daily_results = query.with_entities(
            Expense.expense_date,
            func.sum(Expense.amount).label('amount')
        ).group_by(Expense.expense_date).all()
        
        daily_breakdown = {
            str(result.date): result.amount 
            for result in daily_results
        }
        
        return ExpenseSummary(
            total_amount=total_amount,
            total_count=total_count,
            average_amount=round(average_amount, 2),
            category_breakdown=category_breakdown,
            daily_breakdown=daily_breakdown
        )

    async def get_category_stats(
        self,
        user_id: str,
        trip_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[CategoryStats]:
        """获取费用分类统计"""
        query = self.db.query(Expense).join(Trip).filter(Trip.user_id == user_id)
        
        if trip_id:
            query = query.filter(Expense.trip_id == trip_id)
        if start_date:
            query = query.filter(Expense.expense_date >= start_date)
        if end_date:
            query = query.filter(Expense.expense_date <= end_date)
        
        # 总金额
        total_amount = query.with_entities(func.sum(Expense.amount)).scalar() or 0
        
        # 分类统计
        results = query.with_entities(
            Expense.category,
            func.sum(Expense.amount).label('amount'),
            func.count(Expense.id).label('count')
        ).group_by(Expense.category).all()
        
        stats = []
        for result in results:
            percentage = (result.amount / total_amount * 100) if total_amount > 0 else 0
            stats.append(CategoryStats(
                category=result.category,
                amount=result.amount,
                count=result.count,
                percentage=round(percentage, 2)
            ))
        
        return stats

    async def _update_budget(self, trip_id: str):
        """更新预算信息（预算现在在Trip模型中）"""
        # 计算已花费金额
        spent_amount = self.db.query(func.sum(Expense.amount)).filter(
            Expense.trip_id == trip_id
        ).scalar() or 0
        
        # 注意：预算信息现在直接在Trip模型中
        # 不需要单独更新Budget表（已删除）
        # 如果需要缓存花费金额，可以考虑在Trip模型中添加spent_amount字段
        # 或者在查询时实时计算
        
        # 这里暂时不做任何操作，因为预算统计可以通过查询Expense实时计算
        pass
