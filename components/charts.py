import plotly.graph_objects as go
import database as db


def xp_over_time_chart(user_id):
    rows = db.get_xp_over_time(user_id)
    if not rows:
        return None
    days = [r["day"] for r in rows]
    totals = [r["total"] for r in rows]
    # Cumulative
    cumulative = []
    s = 0
    for t in totals:
        s += abs(t)
        cumulative.append(s)

    fig = go.Figure(go.Scatter(x=days, y=cumulative, mode="lines+markers",
                               line=dict(color="#3498DB", width=2),
                               marker=dict(size=6)))
    fig.update_layout(title="XP Gained Over Time", xaxis_title="Date", yaxis_title="Cumulative XP",
                      height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def category_distribution_chart(user_id):
    rows = db.get_category_completion_counts(user_id)
    if not rows:
        return None
    names = [f"{r['icon']} {r['name']}" for r in rows]
    counts = [r["count"] for r in rows]
    colors = [r["color"] for r in rows]

    fig = go.Figure(go.Pie(labels=names, values=counts, marker=dict(colors=colors),
                           hole=0.4, textinfo="label+value"))
    fig.update_layout(title="Tasks by Category", height=300, margin=dict(l=20, r=20, t=40, b=20),
                      showlegend=False)
    return fig


def weekly_completions_chart(user_id):
    rows = db.get_weekly_completions(user_id)
    if not rows:
        return None
    days = [r["day"] for r in rows]
    counts = [r["count"] for r in rows]

    fig = go.Figure(go.Bar(x=days, y=counts, marker_color="#2ECC71"))
    fig.update_layout(title="Completions (Last 7 Days)", xaxis_title="Date", yaxis_title="Tasks",
                      height=300, margin=dict(l=20, r=20, t=40, b=20))
    return fig
