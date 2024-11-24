# tools/visualization_tool.py

import matplotlib.pyplot as plt
import io
import base64

def draw_bar_chart(data, save_path, title="Bar Chart", xlabel="Category", ylabel="Value"):
    """
    Draws a bar chart from a list of 2-element tuples.

    Args:
        data (list of tuples): Each tuple contains (label, value).
        title (str): Title of the chart.
        xlabel (str): Label for the X-axis.
        ylabel (str): Label for the Y-axis.

    Returns:
        str: Base64-encoded image of the bar chart.
    """
    labels, values = zip(*data)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(labels, values, color='skyblue')
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    # Save the plot to an in-memory bytes buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close(fig)

    # Encode the buffer contents to Base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    with open(save_path, "w") as f:
        f.write(img_base64)
