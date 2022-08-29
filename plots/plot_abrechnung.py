#! /usr/bin/env python3

"""
Plot the graph
"""
from dataclasses import dataclass
from hashlib import md5

from plotly import graph_objects, colors

COLORS = colors.qualitative.Set3

EXAMPLE = [
    ("Schatzinsel", 2000),
    ("Rum", -300),
    ("Rum", -80),
    ("Reparatur", -400),
    ("Kanonen", -20),
    ("Kanonen", -800),
    ("Kanonen", -180),
]


@dataclass
class Node:
    id: int
    label: str
    color: str


@dataclass
class Link:
    source: int
    target: int
    value: float
    color: str


def get_color(string):
    """get a lighter version of the color by index"""
    string_hash = md5()
    string_hash.update(string.encode())
    index = int(string_hash.hexdigest(), 16)
    color = COLORS[index % len(COLORS)]
    return color.replace("rgb", "rgba").replace(")", ",.5)")


def plot(year, input_values):
    """plot"""

    value_map = {}
    for value_type, amount in input_values:
        value_map[value_type] = value_map.get(value_type, 0.) + amount

    income = dict(value_item for value_item in value_map.items() if value_item[1] > 0)
    spending = dict(value_item for value_item in value_map.items() if value_item[1] < 0)

    difference = sum(income.values()) + sum(spending.values())

    if difference > 0:
        spending[f"Rücklagen {year + 1}"] = -difference
    else:
        income[f"Rücklagen {year - 1}"] = -difference

    nodes = {}
    links = []
    for i, (node_type, node_amount) in enumerate((income | spending).items()):
        nodes[node_type] = Node(
            id=i,
            label=f"{node_type} ({abs(node_amount):.2f} €)",
            color=get_color(node_type),
        )

    source = list(income.items())[0][0]

    if len(income) > 1:
        nodes["Budget"] = Node(
            id=len(nodes),
            label=f"Budget ({sum(income.values()):.2f} €)",
            color=get_color("Budget"),
        )
        source = "Budget"

        for income_type, income_amount in income.items():
            links.append(Link(
                source=nodes[income_type].id,
                target=nodes["Budget"].id,
                value=income_amount,
                color=nodes[income_type].color,
            ))

    for spending_type, spending_amount in spending.items():
        links.append(Link(
            source=nodes[source].id,
            target=nodes[spending_type].id,
            value=-spending_amount,
            color=nodes[spending_type].color,
        ))

    nodes_by_id = {node.id: node for node in nodes.values()}

    fig = graph_objects.Figure(data=[
        graph_objects.Sankey(
            valueformat=".02f",
            valuesuffix=" €",
            node=dict(
                pad=15,
                thickness=15,
                line=dict(color="black", width=0.5),
                label=[nodes_by_id[i].label for i in range(len(nodes))],
                color=[nodes_by_id[i].color for i in range(len(nodes))],
            ),
            link=dict(
                source=[link.source for link in links],
                target=[link.target for link in links],
                value=[link.value for link in links],
                color=[link.color for link in links],
            ),
        )
    ])

    fig.update_layout(
        title_text=f"XGME-LAN {year}, Einnahmen und Ausgaben",
        font_size=24,
        autosize=False,
        width=1200,
        height=900,
    )
    fig.write_image(f"Abrechnung{year}.png", engine="kaleido")


if __name__ == "__main__":
    import sys
    import csv

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        data_year = int(filename[filename.index("20"):][:4])
        with open(filename) as infile:
            reader = csv.DictReader(infile, dialect="excel")
            data = [(line["Typ"], float(line["Betrag"].strip(" €").replace('.', '').replace(",", "."))) for line in
                    reader]
    else:
        data_year = 1847
        data = EXAMPLE
    plot(data_year, data)
