"""现金流折现（DCF）估值模型

第一性原理：一项资产的内在价值等于它未来所有现金流的现值之和。

对于房产：
- 未来现金流 = 每年净租金收入
- 折现率 = 无风险利率 + 房产风险溢价
- 终值 = 第N年后的残余价值（基于退出cap rate）

考虑中国特殊因素：
- 70年产权（住宅），到期后的不确定性
- 租金增长率受限于收入增长和CPI
"""
import numpy as np


def calculate_dcf(
    monthly_rent_per_sqm: float,
    area: float = 90,
    discount_rate: float = 0.05,
    rent_growth_rate: float = 0.02,
    vacancy_rate: float = 0.05,
    management_cost_ratio: float = 0.10,
    projection_years: int = 30,
    terminal_cap_rate: float = 0.05,
    remaining_years: int = 70,
    property_fee_per_sqm_month: float = 3.0,
) -> dict:
    """DCF估值

    Args:
        monthly_rent_per_sqm: 当前月租金（元/㎡）
        area: 面积（㎡）
        discount_rate: 折现率
        rent_growth_rate: 租金年增长率
        vacancy_rate: 空置率
        management_cost_ratio: 管理成本（占租金比例，含维修）
        projection_years: 详细预测年数
        terminal_cap_rate: 退出资本化率
        remaining_years: 剩余产权年限
        property_fee_per_sqm_month: 物业费

    Returns:
        估值结果
    """
    annual_gross_rent_psm = monthly_rent_per_sqm * 12
    annual_property_fee_psm = property_fee_per_sqm_month * 12

    cash_flows = []
    yearly_details = []

    for year in range(1, projection_years + 1):
        # 该年租金（含增长）
        gross_rent = annual_gross_rent_psm * (1 + rent_growth_rate) ** (year - 1)
        # 有效租金（扣除空置）
        effective_rent = gross_rent * (1 - vacancy_rate)
        # 运营成本
        operating_cost = effective_rent * management_cost_ratio + annual_property_fee_psm
        # 净经营收入（NOI）
        noi = effective_rent - operating_cost
        # 折现
        pv_factor = 1 / (1 + discount_rate) ** year
        pv = noi * pv_factor

        cash_flows.append(pv)
        if year <= 5 or year == projection_years:
            yearly_details.append({
                "year": year,
                "gross_rent_psm": round(gross_rent, 1),
                "noi_psm": round(noi, 1),
                "pv_psm": round(pv, 1),
            })

    # 终值计算
    # 第N年的NOI
    terminal_noi = (annual_gross_rent_psm * (1 + rent_growth_rate) ** projection_years
                    * (1 - vacancy_rate) * (1 - management_cost_ratio)
                    - annual_property_fee_psm)

    # 产权折扣：如果剩余年限较短，终值需要大幅折扣
    years_left_after_projection = remaining_years - projection_years
    if years_left_after_projection <= 0:
        terminal_value_psm = 0
    else:
        # 终值 = 第N+1年NOI / cap rate
        raw_terminal = terminal_noi / terminal_cap_rate
        # 产权年限折扣
        if years_left_after_projection < 30:
            tenure_discount = years_left_after_projection / 70
        else:
            tenure_discount = 1.0
        terminal_value_psm = raw_terminal * tenure_discount

    pv_terminal = terminal_value_psm / (1 + discount_rate) ** projection_years

    total_pv_rent = sum(cash_flows)
    total_value_psm = total_pv_rent + pv_terminal

    # 三档估值
    # 保守：折现率+1%，增长率-0.5%
    conservative = _quick_dcf(
        annual_gross_rent_psm, discount_rate + 0.01,
        rent_growth_rate - 0.005, vacancy_rate + 0.02,
        management_cost_ratio, projection_years,
        terminal_cap_rate + 0.01, remaining_years,
        annual_property_fee_psm,
    )
    # 乐观：折现率-0.5%，增长率+0.5%
    optimistic = _quick_dcf(
        annual_gross_rent_psm, discount_rate - 0.005,
        rent_growth_rate + 0.005, vacancy_rate - 0.02,
        management_cost_ratio, projection_years,
        terminal_cap_rate - 0.005, remaining_years,
        annual_property_fee_psm,
    )

    return {
        "model": "dcf",
        "model_name": "现金流折现法",
        "fair_value_per_sqm": round(total_value_psm),
        "conservative_value": round(conservative),
        "optimistic_value": round(optimistic),
        "pv_rental_income": round(total_pv_rent),
        "pv_terminal_value": round(pv_terminal),
        "terminal_share": round(pv_terminal / total_value_psm * 100, 1) if total_value_psm > 0 else 0,
        "discount_rate": discount_rate,
        "rent_growth_rate": rent_growth_rate,
        "projection_years": projection_years,
        "yearly_details": yearly_details,
    }


def _quick_dcf(
    annual_gross_rent_psm, discount_rate, growth_rate, vacancy,
    mgmt_ratio, years, term_cap, remaining, prop_fee_annual,
):
    """快速DCF计算（用于生成保守/乐观估值）"""
    total = 0
    for y in range(1, years + 1):
        gross = annual_gross_rent_psm * (1 + growth_rate) ** (y - 1)
        eff = gross * (1 - vacancy)
        noi = eff * (1 - mgmt_ratio) - prop_fee_annual
        total += noi / (1 + discount_rate) ** y

    # 终值
    term_noi = (annual_gross_rent_psm * (1 + growth_rate) ** years
                * (1 - vacancy) * (1 - mgmt_ratio) - prop_fee_annual)
    years_left = remaining - years
    if years_left > 0:
        raw_term = term_noi / term_cap
        tenure_disc = min(years_left / 70, 1.0)
        pv_term = raw_term * tenure_disc / (1 + discount_rate) ** years
        total += pv_term

    return total
