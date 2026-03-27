"""历史回报率计算模型

计算不同时期买入房产的实际回报率，
包含资本增值、租金收入、持有成本，
用IRR（内部收益率）衡量真实投资回报。
"""
import numpy as np
from scipy.optimize import brentq
from utils.database import query_df


def get_historical_prices(city: str, district: str) -> dict:
    """获取历史成交均价"""
    stats = query_df("""
        SELECT month, avg_unit_price, avg_rent_per_sqm
        FROM district_stats
        WHERE city = ? AND district = ?
        ORDER BY month
    """, [city, district])

    if stats.empty:
        return None

    # 按年汇总
    stats["year"] = stats["month"].str[:4].astype(int)
    yearly = stats.groupby("year").agg({
        "avg_unit_price": "mean",
        "avg_rent_per_sqm": "mean",
    }).reset_index()

    return {
        "monthly": stats,
        "yearly": yearly,
    }


def calculate_irr(cash_flows: list) -> float:
    """计算IRR（内部收益率）

    cash_flows: 每期现金流列表，第一个为初始投资（负数）
    """
    if not cash_flows or len(cash_flows) < 2:
        return 0

    # 检查是否全部同号
    positives = sum(1 for cf in cash_flows if cf > 0)
    negatives = sum(1 for cf in cash_flows if cf < 0)
    if positives == 0 or negatives == 0:
        return 0

    def npv(rate):
        return sum(cf / (1 + rate) ** t for t, cf in enumerate(cash_flows))

    try:
        return brentq(npv, -0.5, 5.0)
    except (ValueError, RuntimeError):
        return 0


def calculate_historical_return(
    city: str,
    district: str,
    purchase_year: int,
    purchase_price_per_sqm: float = None,
    area: float = 90,
    down_payment_ratio: float = 0.3,
    mortgage_rate: float = 0.045,
    mortgage_years: int = 30,
    current_year: int = 2025,
    deed_tax_rate: float = 0.015,
    agency_fee_rate: float = 0.015,
    property_fee_per_sqm_month: float = 3.0,
    selling_tax_rate: float = 0.01,
) -> dict:
    """计算历史买入的投资回报

    Args:
        city, district: 城市区域
        purchase_year: 买入年份
        purchase_price_per_sqm: 买入单价（None则用历史均价）
        area: 面积
        down_payment_ratio: 首付比例
        mortgage_rate: 贷款利率
        mortgage_years: 贷款年限
        current_year: 当前年份
        deed_tax_rate: 契税率
        agency_fee_rate: 中介费率
        property_fee_per_sqm_month: 月物业费
        selling_tax_rate: 卖出税费率

    Returns:
        回报分析结果
    """
    hist = get_historical_prices(city, district)
    if hist is None:
        return {"error": "无历史数据"}

    yearly = hist["yearly"]
    years_held = current_year - purchase_year
    if years_held <= 0:
        return {"error": "买入年份必须早于当前年份"}

    # 买入价
    if purchase_price_per_sqm is None:
        yr_data = yearly[yearly["year"] == purchase_year]
        if yr_data.empty:
            return {"error": f"无{purchase_year}年数据"}
        purchase_price_per_sqm = yr_data.iloc[0]["avg_unit_price"]

    # 当前价
    current_data = yearly[yearly["year"] == yearly["year"].max()]
    if current_data.empty:
        return {"error": "无当前价格数据"}
    current_price_per_sqm = current_data.iloc[0]["avg_unit_price"]

    # --- 成本计算 ---
    total_purchase_price = purchase_price_per_sqm * area
    down_payment = total_purchase_price * down_payment_ratio
    loan_amount = total_purchase_price * (1 - down_payment_ratio)

    # 交易费用
    deed_tax = total_purchase_price * deed_tax_rate
    agency_fee = total_purchase_price * agency_fee_rate
    buy_costs = deed_tax + agency_fee

    # 月供（等额本息）
    if loan_amount > 0 and mortgage_rate > 0:
        monthly_rate = mortgage_rate / 12
        total_months = mortgage_years * 12
        monthly_payment = loan_amount * monthly_rate * (1 + monthly_rate) ** total_months / ((1 + monthly_rate) ** total_months - 1)
    else:
        monthly_payment = 0

    # 已还月数
    months_paid = min(years_held * 12, mortgage_years * 12)
    total_mortgage_paid = monthly_payment * months_paid

    # 剩余贷款本金
    remaining_principal = loan_amount
    monthly_rate = mortgage_rate / 12
    for _ in range(months_paid):
        interest = remaining_principal * monthly_rate
        principal_part = monthly_payment - interest
        remaining_principal -= principal_part
    remaining_principal = max(remaining_principal, 0)

    # 持有成本
    annual_property_fee = property_fee_per_sqm_month * 12 * area
    total_property_fee = annual_property_fee * years_held

    # 卖出费用
    current_total_value = current_price_per_sqm * area
    sell_costs = current_total_value * selling_tax_rate

    # --- 收益计算 ---
    # 资本增值
    capital_gain = (current_price_per_sqm - purchase_price_per_sqm) * area

    # 租金收入（按历史租金估算）
    total_rental_income = 0
    for yr in range(purchase_year, current_year):
        yr_rent_data = yearly[yearly["year"] == yr]
        if not yr_rent_data.empty:
            rent_psm = yr_rent_data.iloc[0]["avg_rent_per_sqm"]
        else:
            # 用最近有数据的年份
            rent_psm = yearly["avg_rent_per_sqm"].iloc[-1]
        annual_rent = rent_psm * 12 * area * 0.95  # 扣5%空置
        total_rental_income += annual_rent

    # --- 汇总 ---
    total_cost = down_payment + buy_costs + total_mortgage_paid + total_property_fee
    total_proceeds = current_total_value - remaining_principal - sell_costs
    net_profit = total_proceeds + total_rental_income - total_cost

    # 简单年化回报
    total_investment = down_payment + buy_costs
    total_return = net_profit / total_investment if total_investment > 0 else 0
    annualized_return = (1 + total_return) ** (1 / years_held) - 1 if years_held > 0 else 0

    # IRR计算（以年为单位的现金流）
    cash_flows = [-(down_payment + buy_costs)]  # 初始投资
    for yr in range(purchase_year, current_year):
        yr_rent_data = yearly[yearly["year"] == yr]
        rent_psm = yr_rent_data.iloc[0]["avg_rent_per_sqm"] if not yr_rent_data.empty else yearly["avg_rent_per_sqm"].iloc[-1]
        annual_rent = rent_psm * 12 * area * 0.95
        annual_mortgage = monthly_payment * 12
        annual_prop_fee = annual_property_fee
        net_cf = annual_rent - annual_mortgage - annual_prop_fee
        cash_flows.append(net_cf)

    # 最后一年加上卖出净得
    cash_flows[-1] += total_proceeds

    irr = calculate_irr(cash_flows)

    return {
        "purchase_year": purchase_year,
        "years_held": years_held,
        "purchase_price_per_sqm": round(purchase_price_per_sqm),
        "current_price_per_sqm": round(current_price_per_sqm),
        "price_change_pct": round((current_price_per_sqm / purchase_price_per_sqm - 1) * 100, 1),
        "area": area,
        "costs": {
            "down_payment": round(down_payment),
            "deed_tax": round(deed_tax),
            "agency_fee": round(agency_fee),
            "total_mortgage_paid": round(total_mortgage_paid),
            "property_fee_total": round(total_property_fee),
            "sell_costs": round(sell_costs),
            "total_cost": round(total_cost),
        },
        "income": {
            "capital_gain": round(capital_gain),
            "rental_income": round(total_rental_income),
            "net_proceeds_from_sale": round(total_proceeds),
        },
        "returns": {
            "net_profit": round(net_profit),
            "total_return_pct": round(total_return * 100, 1),
            "annualized_return_pct": round(annualized_return * 100, 2),
            "irr_pct": round(irr * 100, 2),
        },
        "monthly_payment": round(monthly_payment),
        "remaining_principal": round(remaining_principal),
    }


def compare_purchase_years(
    city: str,
    district: str,
    years: list = None,
    area: float = 90,
) -> list:
    """对比不同年份买入的回报率"""
    if years is None:
        years = [2015, 2017, 2019, 2020, 2021, 2022, 2023]

    results = []
    for year in years:
        result = calculate_historical_return(city, district, year, area=area)
        if "error" not in result:
            results.append(result)

    return results
