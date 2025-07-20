import argparse
import sys
import webbrowser
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MaxNLocator

# Add the src directory to the path so we can import wyrdbound_dice
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wyrdbound_dice import Dice


def calculate_dice_statistics(dice_expression: str, num_rolls: int = 10000):
    """Calculate statistics for a dice expression by running simulations."""
    print(f"Rolling {dice_expression} {num_rolls:,} times...")

    results = []
    for i in range(num_rolls):
        if i % 1000 == 0 and i > 0:
            print(f"  Progress: {i:,}/{num_rolls:,} ({i/num_rolls:.1%})")

        roll_result = Dice.roll(dice_expression)
        results.append(roll_result.total)

    # Count frequencies
    counter = Counter(results)
    total_rolls = len(results)

    # Convert to probabilities
    outcomes = sorted(counter.keys())
    probabilities = [counter[outcome] / total_rolls for outcome in outcomes]

    # Calculate statistics
    min_roll = min(results)
    max_roll = max(results)
    avg_roll = sum(results) / len(results)
    most_common = counter.most_common(1)[0]

    return {
        "outcomes": outcomes,
        "probabilities": probabilities,
        "counter": counter,
        "stats": {
            "min": min_roll,
            "max": max_roll,
            "average": avg_roll,
            "most_common": most_common,
            "unique_outcomes": len(outcomes),
            "total_rolls": total_rolls,
        },
    }


def create_dice_graph(
    dice_expression: str, data: dict, output_file: str = "dice_stats.html"
):
    """Create a beautiful graph showing dice roll probabilities."""

    # Set up the plot with a modern style
    plt.style.use(
        "seaborn-v0_8" if "seaborn-v0_8" in plt.style.available else "default"
    )

    # Create figure with custom layout
    fig = plt.figure(figsize=(14, 10))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[0.5, 2, 0.8], width_ratios=[3, 1])

    # Main bar chart
    ax_main = fig.add_subplot(gs[1, 0])

    outcomes = data["outcomes"]
    probabilities = data["probabilities"]
    stats = data["stats"]

    # Create the bar chart with gradient colors
    bars = ax_main.bar(
        outcomes,
        probabilities,
        color="steelblue",
        edgecolor="navy",
        linewidth=0.5,
        alpha=0.8,
    )

    # Add gradient effect to bars
    for i, bar in enumerate(bars):
        # Color gradient from blue to red based on probability
        prob = probabilities[i]
        max_prob = max(probabilities)
        intensity = prob / max_prob if max_prob > 0 else 0
        color = plt.cm.viridis(intensity)
        bar.set_color(color)

    # Customize main chart
    ax_main.set_xlabel("Roll Result", fontsize=12, fontweight="bold")
    ax_main.set_ylabel("Probability", fontsize=12, fontweight="bold")
    ax_main.set_title(
        f"Dice Roll Probability Distribution\n{dice_expression}",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    # Add grid for better readability
    ax_main.grid(axis="y", alpha=0.3, linestyle="--")
    ax_main.set_axisbelow(True)

    # Format y-axis as percentages
    ax_main.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1%}"))

    # Force x-axis labels to be whole integers
    ax_main.xaxis.set_major_locator(MaxNLocator(integer=True))

    # Set x-axis limits based on the outcome values
    ax_main.set_xlim(min(outcomes) - 0.5, max(outcomes) + 0.5)

    # Add value labels on top of bars if there aren't too many
    if len(outcomes) <= 20:
        for outcome, prob in zip(outcomes, probabilities):
            ax_main.text(
                outcome,
                prob + max(probabilities) * 0.01,
                f"{prob:.1%}",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
            )

    # Statistics panel
    ax_stats = fig.add_subplot(gs[1, 1])
    ax_stats.axis("off")

    # Replace Unicode characters with Arial-compatible text
    ax_main.set_title(
        f"Dice Roll Probability Distribution\n{dice_expression}",
        fontsize=16,
        fontweight="bold",
        pad=20,
    )

    stats_text = f"""
STATISTICS

Expression: {dice_expression}
Total Rolls: {stats['total_rolls']:,}

Range: {stats['min']} - {stats['max']}
Average: {stats['average']:.2f}
Most Common: {stats['most_common'][0]}
   ({stats['most_common'][1]:,} times)
   ({stats['most_common'][1]/stats['total_rolls']:.1%})
Unique Results: {stats['unique_outcomes']}

Standard Deviation: {(sum((x - stats['average'])**2 for x in data['counter'].elements()) / stats['total_rolls'])**0.5:.2f}
    """.strip()

    ax_stats.text(
        0.05,
        0.95,
        stats_text,
        transform=ax_stats.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8),
    )

    # Title section
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    ax_title.text(
        0.5,
        0.5,
        "Dice Statistics Visualizer",
        transform=ax_title.transAxes,
        fontsize=20,
        fontweight="bold",
        horizontalalignment="center",
        verticalalignment="center",
    )

    # Footer with theoretical vs actual
    ax_footer = fig.add_subplot(gs[2, :])
    ax_footer.axis("off")

    # Calculate theoretical probabilities for simple dice (if applicable)
    footer_text = f"Simulated with {stats['total_rolls']:,} rolls • "

    # Try to determine if this is a simple die roll for comparison
    if (
        dice_expression.replace(" ", "").startswith("1d")
        and "+" not in dice_expression
        and "-" not in dice_expression
    ):
        try:
            sides = int(dice_expression.split("d")[1])
            theoretical_prob = 1.0 / sides
            footer_text += (
                f"Theoretical probability per outcome: {theoretical_prob:.1%} • "
            )
        except (ValueError, IndexError, ZeroDivisionError):
            pass

    footer_text += "Generated with matplotlib"

    ax_footer.text(
        0.5,
        0.5,
        footer_text,
        transform=ax_footer.transAxes,
        fontsize=9,
        style="italic",
        horizontalalignment="center",
        verticalalignment="center",
    )

    plt.tight_layout()

    # Save as HTML file that will auto-open in browser
    html_file = Path(output_file)

    # Save the plot as PNG first
    png_file = html_file.with_suffix(".png")
    plt.savefig(
        png_file, dpi=300, bbox_inches="tight", facecolor="white", edgecolor="none"
    )

    # Generate HTML table for outcomes and probabilities
    # Update HTML table to include occurrences along with probabilities
    table_rows = "".join(
        f"<tr><td>{outcome}</td><td>{prob:.1%}</td><td>{data['counter'][outcome]}</td></tr>"
        for outcome, prob in zip(data["outcomes"], data["probabilities"])
    )

    table_html = f"""
    <div class='table-container'>
        <h3>📊 Results Table:</h3>
        <table>
            <thead>
                <tr>
                    <th>Outcome</th>
                    <th>Probability</th>
                    <th>Occurrences</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
    </div>
    """

    # Add three example rolls to the HTML output
    example_rolls = [str(Dice.roll(dice_expression)) for _ in range(3)]

    # Update HTML content to include the table
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dice Statistics - {dice_expression}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            max-width: 1200px;
            width: 100%;
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .graph-container {{
            text-align: center;
            margin: 20px 0;
        }}
        .graph-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }}
        .instructions {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            border-left: 4px solid #667eea;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-style: italic;
        }}
        .table-container {{
            margin-top: 20px;
            text-align: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #667eea;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        .example-rolls {{
            background: #eef9ff;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
            text-align: left;
            border-left: 4px solid #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎲 Dice Statistics for "{dice_expression}"</h1>

        <div class="graph-container">
            <img src="{png_file.name}" alt="Dice Statistics Graph">
        </div>

        {table_html}

        <div class="instructions">
            <h3>📖 How to Read This Graph:</h3>
            <ul>
                <li><strong>X-axis:</strong> Possible roll results</li>
                <li><strong>Y-axis:</strong> Probability of each result (as percentage)</li>
                <li><strong>Bar colors:</strong> Intensity represents relative probability</li>
                <li><strong>Statistics panel:</strong> Summary of roll distribution</li>
            </ul>

            <h3>🎯 Key Insights:</h3>
            <ul>
                <li>Most likely result: <strong>{data['stats']['most_common'][0]}</strong> ({data['stats']['most_common'][1]/data['stats']['total_rolls']:.1%} chance)</li>
                <li>Average roll: <strong>{data['stats']['average']:.2f}</strong></li>
                <li>Range: <strong>{data['stats']['min']}</strong> to <strong>{data['stats']['max']}</strong></li>
            </ul>
        </div>

        <div class="example-rolls" style="text-align: left;">
            <h3>🎲 Example Rolls:</h3>
            <ul>
                {''.join(f'<li>{roll}</li>' for roll in example_rolls)}
            </ul>
        </div>

        <div class="footer">
            Generated by running {data['stats']['total_rolls']:,} simulated dice rolls
        </div>
    </div>
</body>
</html>
    """

    # Write HTML file
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    plt.close()

    return html_file


def main():
    """Main function to run dice statistics visualization."""
    parser = argparse.ArgumentParser(
        description="Generate dice roll statistics visualization"
    )
    parser.add_argument(
        "expression",
        nargs="?",
        default="1d6",
        help="Dice expression to analyze (e.g., 1d6, 2d10+3, 3d4-1)",
    )
    parser.add_argument(
        "-n",
        "--num-rolls",
        type=int,
        default=10000,
        help="Number of rolls to simulate (default: 10000)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="dice_stats.html",
        help="Output HTML file name (default: dice_stats.html)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't automatically open browser"
    )

    args = parser.parse_args()

    try:

        # Validate the dice expression by trying to roll it once
        test_roll = Dice.roll(args.expression)
        print(f"✅ Valid dice expression: {args.expression}")
        print(f"📝 Test roll result: {test_roll}")
        print()

        # Calculate statistics
        data = calculate_dice_statistics(args.expression, args.num_rolls)

        # Create and save the graph
        print("\n🎨 Creating visualization...")
        html_file = create_dice_graph(args.expression, data, args.output)

        print(f"✅ Graph saved as: {html_file}")
        print("📊 Statistics:")
        print(f"   Range: {data['stats']['min']} - {data['stats']['max']}")
        print(f"   Average: {data['stats']['average']:.2f}")
        print(
            f"   Most common: {data['stats']['most_common'][0]} ({data['stats']['most_common'][1]/data['stats']['total_rolls']:.1%})"
        )

        # Open in browser
        if not args.no_browser:
            print(f"\n🌐 Opening {html_file} in browser...")
            webbrowser.open(f"file://{Path(html_file).absolute()}")
        else:
            print(f"\n💡 To view the graph, open: file://{Path(html_file).absolute()}")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure your dice expression is valid (e.g., 1d6, 2d10+3, 3d4-1)")
        return 1

    return 0


if __name__ == "__main__":
    result = main()
    exit(result)
