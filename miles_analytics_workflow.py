#!/usr/bin/env python3
"""
Miles Analytics Workflow - Demonstrates full MCP capabilities
Combines database analytics, web automation, and data processing
"""

from datetime import datetime
from typing import Any

import duckdb


def export_data_to_csv() -> str:
    """Export DuckDB data to CSV for analysis."""
    print("📤 Exporting data to CSV...")

    conn = duckdb.connect("miles_analytics.duckdb")

    # Export bot usage analytics
    df_usage = conn.execute(
        """
        SELECT 
            DATE(timestamp) as date,
            command,
            COUNT(*) as usage_count,
            AVG(response_time_sec) as avg_response_time,
            SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
        FROM bot_usage 
        GROUP BY DATE(timestamp), command
        ORDER BY date DESC, usage_count DESC
    """
    ).df()

    # Export promotion analytics
    df_promos = conn.execute(
        """
        SELECT 
            DATE(date_found) as date,
            program,
            source,
            AVG(bonus_percentage) as avg_bonus,
            COUNT(*) as promo_count,
            SUM(CASE WHEN alert_sent THEN 1 ELSE 0 END) as alerts_sent
        FROM promotions
        GROUP BY DATE(date_found), program, source
        ORDER BY date DESC, avg_bonus DESC
    """
    ).df()

    conn.close()

    # Save to CSV files
    usage_file = "all_pdfs/bot_usage_analytics.csv"
    promo_file = "all_pdfs/promotion_analytics.csv"

    df_usage.to_csv(usage_file, index=False, sep=";")
    df_promos.to_csv(promo_file, index=False, sep=";")

    print(f"✅ Exported {len(df_usage)} usage records to {usage_file}")
    print(f"✅ Exported {len(df_promos)} promotion records to {promo_file}")

    return usage_file, promo_file


def analyze_performance_trends() -> dict[str, Any]:
    """Analyze Miles bot performance trends."""
    print("📊 Analyzing performance trends...")

    conn = duckdb.connect("miles_analytics.duckdb")

    # Daily success rate trend
    daily_performance = conn.execute(
        """
        SELECT 
            DATE(timestamp) as date,
            COUNT(*) as total_commands,
            AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
            AVG(response_time_sec) as avg_response_time
        FROM bot_usage 
        GROUP BY DATE(timestamp)
        ORDER BY date
    """
    ).fetchall()

    # Command efficiency analysis
    command_efficiency = conn.execute(
        """
        SELECT 
            command,
            COUNT(*) as usage_count,
            AVG(response_time_sec) as avg_time,
            AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
            COUNT(DISTINCT user_id) as unique_users
        FROM bot_usage 
        GROUP BY command
        ORDER BY usage_count DESC
    """
    ).fetchall()

    # Best promotion sources
    best_sources = conn.execute(
        """
        SELECT 
            source,
            COUNT(*) as total_promos,
            AVG(bonus_percentage) as avg_bonus,
            COUNT(*) * AVG(bonus_percentage) as value_score
        FROM promotions
        GROUP BY source
        ORDER BY value_score DESC
    """
    ).fetchall()

    conn.close()

    analysis = {
        "daily_performance": daily_performance,
        "command_efficiency": command_efficiency,
        "best_sources": best_sources,
        "analysis_timestamp": datetime.now().isoformat(),
    }

    return analysis


def create_insights_report(analysis: dict[str, Any]) -> str:
    """Generate a comprehensive insights report."""
    print("📋 Creating insights report...")

    report = []
    report.append("# 🚀 MILES BOT ANALYTICS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 50)

    # Command efficiency insights
    report.append("\\n## 📈 Command Performance Insights")
    for cmd_data in analysis["command_efficiency"]:
        cmd, usage, avg_time, success_rate, users = cmd_data
        efficiency_score = (success_rate / 100) * (users / usage) * (1 / avg_time)

        if efficiency_score > 0.1:
            status = "🟢 Excellent"
        elif efficiency_score > 0.05:
            status = "🟡 Good"
        else:
            status = "🔴 Needs Improvement"

        report.append(f"- **{cmd}**: {status}")
        report.append(f"  - Usage: {usage} times by {users} users")
        report.append(f"  - Success Rate: {success_rate:.1f}%")
        report.append(f"  - Avg Response: {avg_time:.2f}s")

    # Promotion source analysis
    report.append("\\n## 💰 Best Promotion Sources")
    for source_data in analysis["best_sources"]:
        source, total, avg_bonus, score = source_data
        report.append(
            f"- **{source}**: {total} promos, {avg_bonus:.1f}% avg bonus (Score: {score:.0f})"
        )

    # Performance trends
    report.append("\\n## 📊 Performance Trends")
    daily_data = analysis["daily_performance"]
    if len(daily_data) >= 2:
        latest = daily_data[-1]
        previous = daily_data[-2]

        success_trend = latest[2] - previous[2]
        time_trend = latest[3] - previous[3]

        trend_emoji = "📈" if success_trend > 0 else "📉"
        time_emoji = "⚡" if time_trend < 0 else "🐌"

        report.append(
            f"- Success Rate: {latest[2]:.1f}% {trend_emoji} ({success_trend:+.1f}%)"
        )
        report.append(
            f"- Response Time: {latest[3]:.2f}s {time_emoji} ({time_trend:+.2f}s)"
        )

    # Recommendations
    report.append("\\n## 🎯 Recommendations")

    # Find slowest command
    slowest_cmd = max(analysis["command_efficiency"], key=lambda x: x[2])
    report.append(
        f"- **Optimize {slowest_cmd[0]}**: Currently {slowest_cmd[2]:.2f}s avg response time"
    )

    # Find least successful command
    least_successful = min(analysis["command_efficiency"], key=lambda x: x[3])
    report.append(
        f"- **Improve {least_successful[0]}**: Only {least_successful[3]:.1f}% success rate"
    )

    # Best source recommendation
    best_source = analysis["best_sources"][0]
    report.append(
        f"- **Focus on {best_source[0]}**: Best value source with {best_source[1]} promos"
    )

    report_content = "\\n".join(report)

    # Save report
    report_file = "all_pdfs/miles_analytics_report.md"
    with open(report_file, "w") as f:
        f.write(report_content)

    print(f"✅ Report saved to {report_file}")
    return report_file


def main():
    """Run the complete analytics workflow."""
    print("🚀 MILES ANALYTICS WORKFLOW STARTING...")
    print("=" * 50)

    try:
        # Step 1: Export data
        usage_file, promo_file = export_data_to_csv()

        # Step 2: Analyze trends
        analysis = analyze_performance_trends()

        # Step 3: Create insights report
        report_file = create_insights_report(analysis)

        # Step 4: Summary
        print("\\n🎯 WORKFLOW COMPLETE!")
        print("📁 Files created in all_pdfs/:")
        print(f"  - {usage_file}")
        print(f"  - {promo_file}")
        print(f"  - {report_file}")

        print("\\n🚀 What's next?")
        print("  1. Import these CSVs into PostgreSQL via MCP")
        print("  2. Use Playwright to scrape real promotion data")
        print("  3. Set up automated reporting workflows")
        print("  4. Create real-time dashboards")

        return True

    except Exception as e:
        print(f"❌ Workflow failed: {e!s}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
