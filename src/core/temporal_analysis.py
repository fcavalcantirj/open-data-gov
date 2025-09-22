"""
Temporal Pattern Detection
Implementation of Script 3 from brazilian-political-data-architecture-v0.md

Detects behavioral changes over time in voting patterns and expenses.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import statistics
from collections import defaultdict, Counter


def sliding_window(data: List[Dict], window_size: str = '3_months') -> List[Dict]:
    """
    Create sliding windows for temporal analysis
    """
    if window_size == '3_months':
        window_days = 90
    elif window_size == '6_months':
        window_days = 180
    else:
        window_days = 90  # default

    windows = []
    if not data:
        return windows

    # Sort data by date
    sorted_data = sorted(data, key=lambda x: datetime.fromisoformat(
        x.get('dataHoraRegistro', x.get('dataHoraVoto', x.get('data', '2023-01-01')))
        .replace('Z', '+00:00')
    ))

    # Create windows
    start_date = datetime.fromisoformat(
        sorted_data[0].get('dataHoraRegistro', sorted_data[0].get('dataHoraVoto', sorted_data[0].get('data', '2023-01-01')))
        .replace('Z', '+00:00')
    )

    current_date = start_date
    end_date = datetime.fromisoformat(
        sorted_data[-1].get('dataHoraRegistro', sorted_data[-1].get('dataHoraVoto', sorted_data[-1].get('data', '2023-12-31')))
        .replace('Z', '+00:00')
    )

    while current_date < end_date:
        window_end = current_date + timedelta(days=window_days)

        window_data = [
            item for item in sorted_data
            if current_date <= datetime.fromisoformat(
                item.get('dataHoraRegistro', item.get('dataHoraVoto', item.get('data', '2023-01-01')))
                .replace('Z', '+00:00')
            ) < window_end
        ]

        if window_data:
            windows.append({
                'period': f"{current_date.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}",
                'start_date': current_date,
                'end_date': window_end,
                'data': window_data
            })

        current_date += timedelta(days=30)  # Move window by 1 month

    return windows


def calculate_voting_pattern(window_data: List[Dict]) -> Dict[str, float]:
    """
    Calculate voting pattern metrics for a time window
    """
    if not window_data:
        return {'yes_rate': 0, 'no_rate': 0, 'abstention_rate': 0, 'total_votes': 0}

    votes = window_data
    total_votes = len(votes)

    yes_votes = sum(1 for v in votes if v.get('voto', '').lower() in ['sim', 'yes'])
    no_votes = sum(1 for v in votes if v.get('voto', '').lower() in ['não', 'nao', 'no'])
    abstentions = sum(1 for v in votes if v.get('voto', '').lower() in ['abstenção', 'abstencao', 'abstention'])

    return {
        'yes_rate': yes_votes / total_votes if total_votes > 0 else 0,
        'no_rate': no_votes / total_votes if total_votes > 0 else 0,
        'abstention_rate': abstentions / total_votes if total_votes > 0 else 0,
        'total_votes': total_votes,
        'government_alignment': yes_votes / max(yes_votes + no_votes, 1)  # Simplified
    }


def pattern_divergence(pattern1: Dict, pattern2: Dict) -> float:
    """
    Calculate divergence between two voting patterns
    """
    if not pattern1 or not pattern2:
        return 0.0

    # Calculate Euclidean distance between patterns
    divergence = 0.0
    metrics = ['yes_rate', 'no_rate', 'abstention_rate', 'government_alignment']

    for metric in metrics:
        diff = pattern1.get(metric, 0) - pattern2.get(metric, 0)
        divergence += diff ** 2

    return divergence ** 0.5


def find_potential_trigger(date: datetime) -> str:
    """
    Identify potential triggers for behavioral changes
    Simple implementation - would be enhanced with news/event data
    """
    # Major Brazilian political events (simplified)
    triggers = [
        ("2023-01-08", "Congress Attack"),
        ("2023-01-01", "New Government"),
        ("2022-10-30", "Election Results"),
        ("2022-10-02", "First Round Election"),
    ]

    for trigger_date, event in triggers:
        trigger_datetime = datetime.fromisoformat(trigger_date)
        if abs((date - trigger_datetime).days) <= 30:  # Within 30 days
            return event

    return "Unknown trigger"


def detect_expense_anomalies(expenses: List[Dict]) -> List[Dict]:
    """
    Detect anomalies in expense patterns
    """
    if not expenses:
        return []

    anomalies = []

    # Group expenses by month
    monthly_expenses = defaultdict(list)
    for expense in expenses:
        try:
            date_str = expense.get('dataDocumento', expense.get('data', '2023-01-01'))
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            month_key = date.strftime('%Y-%m')

            value = float(expense.get('valorLiquido', expense.get('valor', 0)))
            monthly_expenses[month_key].append(value)
        except:
            continue

    # Calculate monthly totals
    monthly_totals = {month: sum(values) for month, values in monthly_expenses.items()}

    if len(monthly_totals) < 3:
        return anomalies

    # Calculate statistics
    amounts = list(monthly_totals.values())
    mean_amount = statistics.mean(amounts)
    stdev_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0

    # Find anomalies (2 standard deviations from mean)
    threshold = mean_amount + (2 * stdev_amount)

    for month, total in monthly_totals.items():
        if total > threshold:
            anomalies.append({
                'month': month,
                'amount': total,
                'deviation': (total - mean_amount) / stdev_amount if stdev_amount > 0 else 0,
                'type': 'high_spending'
            })

    return anomalies


def calculate_network_position(deputy_id: str, votes: List[Dict]) -> Dict[str, float]:
    """
    Calculate network position metrics
    Simplified version - would require full network data
    """
    if not votes:
        return {'influence_score': 0.0, 'centrality': 0.0}

    # Simple influence calculation based on vote frequency and patterns
    total_votes = len(votes)
    unique_sessions = len(set(v.get('id', '') for v in votes))

    # Participation rate as proxy for influence
    participation_rate = total_votes / max(unique_sessions, 1)

    return {
        'influence_score': min(participation_rate, 1.0),
        'centrality': 0.5,  # Placeholder - would calculate from network
        'activity_level': total_votes
    }


def analyze_temporal_patterns(entity_id: str, entity_type: str = 'deputy') -> Dict[str, Any]:
    """
    Detect behavioral changes over time
    Implementation of Script 3 from the architecture document
    """

    print(f"\n=== TEMPORAL PATTERN ANALYSIS ===")
    print(f"Entity: {entity_id} (Type: {entity_type})")

    if entity_type != 'deputy':
        return {'error': 'Only deputy analysis implemented'}

    try:
        # === VOTING PATTERN SHIFTS ===
        print("\n--- Voting Pattern Analysis ---")

        # Fetch voting history
        votes_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{entity_id}/votacoes"
        response = requests.get(votes_url, params={"itens": 200})  # More votes for analysis
        response.raise_for_status()

        voting_history = response.json().get('dados', [])
        print(f"✓ Retrieved {len(voting_history)} votes")

        if voting_history:
            # Create sliding windows
            windows = sliding_window(voting_history, window_size='3_months')
            print(f"✓ Created {len(windows)} temporal windows")

            pattern_shifts = []
            for i, window in enumerate(windows[:-1]):
                current_pattern = calculate_voting_pattern(window['data'])
                next_pattern = calculate_voting_pattern(windows[i+1]['data'])

                divergence = pattern_divergence(current_pattern, next_pattern)
                THRESHOLD = 0.2  # Significant change threshold

                if divergence > THRESHOLD:
                    # Something changed - investigate
                    trigger = find_potential_trigger(window['end_date'])
                    pattern_shifts.append({
                        'period': window['period'],
                        'divergence': divergence,
                        'trigger': trigger,
                        'before_pattern': current_pattern,
                        'after_pattern': next_pattern
                    })

                    print(f"  🚨 Pattern shift detected: {window['period']}")
                    print(f"     Divergence: {divergence:.3f}, Trigger: {trigger}")

        # === EXPENSE PATTERN CHANGES ===
        print("\n--- Expense Pattern Analysis ---")

        # Fetch expense timeline
        expenses_url = f"https://dadosabertos.camara.leg.br/api/v2/deputados/{entity_id}/despesas"
        current_year = datetime.now().year

        all_expenses = []
        for year in [current_year, current_year - 1]:
            try:
                params = {"ano": year, "itens": 200}
                response = requests.get(expenses_url, params=params)
                response.raise_for_status()

                year_expenses = response.json().get('dados', [])
                all_expenses.extend(year_expenses)
            except:
                continue

        print(f"✓ Retrieved {len(all_expenses)} expense records")

        anomalies = detect_expense_anomalies(all_expenses)
        print(f"✓ Detected {len(anomalies)} expense anomalies")

        for anomaly in anomalies:
            print(f"  💰 {anomaly['month']}: R$ {anomaly['amount']:,.2f} "
                  f"({anomaly['deviation']:.1f}σ above normal)")

        # === NETWORK POSITION EVOLUTION ===
        print("\n--- Network Position Evolution ---")

        # Calculate monthly network positions
        monthly_networks = []
        months = []

        # Group votes by month for the last 12 months
        monthly_votes = defaultdict(list)
        for vote in voting_history:
            try:
                date_str = vote.get('dataHoraVoto', vote.get('data', '2023-01-01'))
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                month_key = date.strftime('%Y-%m')
                monthly_votes[month_key].append(vote)
            except:
                continue

        for month, votes in sorted(monthly_votes.items()):
            position = calculate_network_position(entity_id, votes)
            monthly_networks.append(position)
            months.append(month)

        print(f"✓ Calculated network positions for {len(monthly_networks)} months")

        # Calculate influence trajectory
        if monthly_networks:
            influence_scores = [pos['influence_score'] for pos in monthly_networks]
            if len(influence_scores) > 1:
                trend = "increasing" if influence_scores[-1] > influence_scores[0] else "decreasing"
                avg_change = (influence_scores[-1] - influence_scores[0]) / len(influence_scores)
                print(f"  📈 Influence trend: {trend} (avg change: {avg_change:+.3f} per month)")

        # Compile results
        result = {
            'entity_id': entity_id,
            'analysis_timestamp': datetime.now().isoformat(),
            'voting_shifts': pattern_shifts,
            'expense_anomalies': anomalies,
            'influence_trajectory': {
                'months': months,
                'positions': monthly_networks,
                'trend': trend if 'trend' in locals() else 'stable'
            },
            'summary': {
                'total_votes_analyzed': len(voting_history),
                'total_expenses_analyzed': len(all_expenses),
                'pattern_shifts_detected': len(pattern_shifts),
                'expense_anomalies_detected': len(anomalies),
                'analysis_period_months': len(monthly_networks)
            }
        }

        print(f"\n✅ TEMPORAL ANALYSIS COMPLETE")
        print(f"   Pattern shifts: {len(pattern_shifts)}")
        print(f"   Expense anomalies: {len(anomalies)}")
        print(f"   Months analyzed: {len(monthly_networks)}")

        return result

    except Exception as e:
        print(f"✗ Error in temporal analysis: {e}")
        return {'error': str(e)}


if __name__ == "__main__":
    # Test temporal analysis with a sample deputy
    # Using Arthur Lira (Chamber President) as in the main discovery script

    print("🕐 TEMPORAL PATTERN DETECTION TEST")
    print("=" * 50)

    # First, get a deputy ID
    try:
        response = requests.get(
            "https://dadosabertos.camara.leg.br/api/v2/deputados",
            params={"nome": "Arthur Lira"}
        )
        response.raise_for_status()
        deputies = response.json().get('dados', [])

        if deputies:
            deputy_id = deputies[0]['id']
            deputy_name = deputies[0]['nome']

            print(f"Testing with: {deputy_name} (ID: {deputy_id})")

            # Run temporal analysis
            analysis_result = analyze_temporal_patterns(deputy_id)

            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"temporal_analysis_{deputy_id}_{timestamp}.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(analysis_result, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n📄 Results saved to: {filename}")

        else:
            print("❌ No deputy found for testing")

    except Exception as e:
        print(f"❌ Test failed: {e}")