import os
from pyvis.network import Network

def generate_html_inline (network, save_path=None):
    """
    Generates a self-contained HTML string for  embedding utils.js.
    Optionally saves it to a file.

    Returns:
        str: self contained HTML string of the graph.
    """
    network.cdn_resources="in_line"
    html_content = network.generate_html(local=False)

    # Locate the utils.js file in the Pyvis package
    try:
        import pyvis
        utils_js_path = os.path.join(os.path.dirname(pyvis.__file__), "lib", "bindings", "utils.js")
        with open(utils_js_path, "r") as js_file:
            utils_js_content = js_file.read()
    except FileNotFoundError:
        raise FileNotFoundError("The utils.js file was not found.")

    # Replace the local.js <script> embedding utils.js content
    html_content = html_content.replace(
        '<script src="lib/bindings/utils.js"></script>',
        f'<script type="text/javascript">{utils_js_content}</script>'
    )

    if save_path:
        with open(save_path, "w") as file:
            file.write(html_content)
        print(f"self ontained graph saved to: {save_path}")

    return html_content


def example():
    net = Network()

    net.add_node(1, label="hello")
    net.add_node(2, label="world")
    net.add_node(3, label="!")
    net.add_edge(1, 2)
    net.add_edge(2, 3)

    net.set_options("""
    var options = {
      "nodes": {
        "shape": "dot",
        "size": 30,
        "font": {
          "size": 32,
          "color": "#000000"
        },
        "borderWidth": 2
      },
      "edges": {
        "width": 2
      }
    }
    """)

    output_html_file = "self_contained_example.html"
    html_string = generate_html_inline(net, save_path=output_html_file)

    return html_string


if __name__ == "__main__":
    example()
