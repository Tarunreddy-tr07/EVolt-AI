"""
utils/visualization.py
-----------------------
Plotly visualization utilities for the Streamlit frontend.
Creates interactive, visually rich graphs for:
  - TOU pricing & simulated power demand curves
  - SoC charging progression
  - Battery degradation & SoH projections
  - RL reward & agent metric performance
"""

from __future__ import annotations

from typing import List, Dict, Tuple
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

from reinforcement_learning.state_space import TOU_PRICE_SCHEDULE, GRID_CAPACITY_KW


def create_tou_price_chart() -> go.Figure:
    """Plot the 24-hour Time-Of-Use electricity tariff schedule."""
    hours = list(range(24))
    prices = [TOU_PRICE_SCHEDULE[h] for h in hours]
    hour_labels = [f"{h:02d}:00" for h in hours]

    colors = []
    for h in hours:
        if 17 <= h < 21:
            colors.append("#EF4444")  # Peak (Red)
        elif 0 <= h < 6:
            colors.append("#10B981")  # Off-Peak (Green)
        else:
            colors.append("#F59E0B")  # Mid-Peak (Amber)

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=hour_labels,
            y=prices,
            marker_color=colors,
            text=[f"${p:.2f}" for p in prices],
            textposition="auto",
            hovertemplate="<b>Hour:</b> %{x}<br><b>Tariff:</b> $%{y:.2f}/kWh<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>24-Hour Time-of-Use (TOU) Electricity Pricing Schedule</b>",
        xaxis_title="Time of Day",
        yaxis_title="Price ($ / kWh)",
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig


def create_slot_soc_barchart(slots: List[Dict]) -> go.Figure:
    """Create horizontal bar chart showing State of Charge (SoC) for all charging slots."""
    slot_labels = [f"Slot #{s['slot_id']} ({'Occupied' if s['occupied'] else 'Available'})" for s in slots]
    soc_pcts = [s["soc_pct"] if s["occupied"] else 0 for s in slots]
    colors = [
        "#10B981" if s["soc_pct"] >= 80 else ("#3B82F6" if s["soc_pct"] >= 40 else "#F59E0B")
        if s["occupied"] else "#374151"
        for s in slots
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=soc_pcts,
            y=slot_labels,
            orientation="h",
            marker_color=colors,
            text=[f"{p:.1f}%" if p > 0 else "0%" for p in soc_pcts],
            textposition="inside",
            hovertemplate="<b>%{y}</b><br>SoC: %{x:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="<b>Live Bay State of Charge (SoC) Levels</b>",
        xaxis=dict(range=[0, 100], title="Battery State of Charge (%)"),
        yaxis=dict(autorange="reversed"),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=45, b=20),
        height=260,
    )
    return fig


def create_soc_curve_plot(times: List[float], soc_vals: List[float], vehicle_name: str = "Vehicle") -> go.Figure:
    """Plot continuous battery charging curve predicted by the ML model."""
    soc_pcts = [s * 100 for s in soc_vals]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=times,
            y=soc_pcts,
            mode="lines+markers",
            name="Predicted SoC",
            line=dict(color="#3B82F6", width=3),
            marker=dict(size=6, color="#60A5FA"),
            hovertemplate="<b>Elapsed:</b> %{x:.2f} hrs<br><b>SoC:</b> %{y:.1f}%<extra></extra>",
        )
    )

    # Add 80% CC/CV transition marker
    fig.add_hline(
        y=80, line_dash="dash", line_color="#F59E0B",
        annotation_text="80% Constant-Voltage Taper Phase", annotation_position="bottom right"
    )

    fig.update_layout(
        title=f"<b>Predicted Charging Curve (ML Model) — {vehicle_name}</b>",
        xaxis_title="Charging Dwell Time (Hours)",
        yaxis_title="Battery State of Charge (%)",
        yaxis=dict(range=[0, 105]),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
        height=350,
    )
    return fig


def create_soh_trend_plot(cycles: List[int], soh_vals: List[float], vehicle_name: str = "Vehicle") -> go.Figure:
    """Plot battery degradation forecast (State of Health)."""
    soh_pcts = [s * 100 for s in soh_vals]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=cycles,
            y=soh_pcts,
            mode="lines",
            name="SoH Degradation Forecast",
            line=dict(color="#10B981", width=3),
            hovertemplate="<b>Cycle Count:</b> %{x}<br><b>Capacity Retention:</b> %{y:.2f}%<extra></extra>",
        )
    )

    # 80% EOL threshold line
    fig.add_hline(
        y=80, line_dash="dash", line_color="#EF4444",
        annotation_text="80% End-of-Life (EOL) Threshold", annotation_position="top right"
    )

    fig.update_layout(
        title=f"<b>Battery Health (SoH) Lifetime Degradation Forecast — {vehicle_name}</b>",
        xaxis_title="Charge / Discharge Cycle Count",
        yaxis_title="State of Health (%)",
        yaxis=dict(range=[60, 105]),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
        height=350,
    )
    return fig


def create_grid_power_profile(power_history: List[float]) -> go.Figure:
    """Plot simulated grid power draw over timesteps."""
    steps = list(range(len(power_history)))
    hours = [s * 0.25 for s in steps]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hours,
            y=power_history,
            mode="lines",
            fill="tozeroy",
            name="Fleet Power Draw",
            line=dict(color="#06B6D4", width=2),
            fillcolor="rgba(6, 182, 212, 0.15)",
            hovertemplate="<b>Hour:</b> %{x:.2f}<br><b>Total Power:</b> %{y:.1f} kW<extra></extra>",
        )
    )

    fig.add_hline(
        y=GRID_CAPACITY_KW, line_dash="dash", line_color="#EF4444",
        annotation_text=f"Transformer Limit ({GRID_CAPACITY_KW:.1f} kW)", annotation_position="top left"
    )

    fig.update_layout(
        title="<b>Live Grid Load Profile (Power Draw vs Transformer Limit)</b>",
        xaxis_title="Simulated Day Time (Hours)",
        yaxis_title="Total Power (kW)",
        yaxis=dict(range=[0, GRID_CAPACITY_KW * 1.15]),
        template="plotly_dark",
        margin=dict(l=40, r=40, t=50, b=40),
        height=320,
    )
    return fig
