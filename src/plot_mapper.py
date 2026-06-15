import itertools
import networkx as nx
import plotly.graph_objects as go


############ Compute graph and vertices position


def compute_x_positions(names_order, spacing):
    # Helper: x-positions for an ordering
    n = len(names_order)
    return {name: ( (j - n/2) * spacing ) for j, name in enumerate(names_order)}



def optimise_order_two_first_layers(list_clusters, spacing, G):
    """For layers 0 and 1, check all permutations to minimise the total weighted horizontal edge length"""
    
    # Assuming list_clusters has at least two layers
    layer0_names = list(list_clusters[0].keys())
    layer1_names = list(list_clusters[1].keys())
    
    best_cost = float('inf')
    best_perm0, best_perm1 = layer0_names, layer1_names
    
    for perm0 in itertools.permutations(layer0_names):
        x0_map = compute_x_positions(list(perm0), spacing)
        for perm1 in itertools.permutations(layer1_names):
            x1_map = compute_x_positions(list(perm1), spacing)
            cost = 0
            # sum weighted horizontal distances of edges connecting layer0 <-> layer1
            for u, v, data in G.edges(data=True):
                lu, lv = G.nodes[u]['layer'], G.nodes[v]['layer']
                if {lu, lv} == {0, 1}:
                    weight = data.get('weight', 1)
                    if lu == 0:
                        cost += weight * abs(x0_map[u.split(":",1)[1]] - x1_map[v.split(":",1)[1]])
                    else:
                        cost += weight * abs(x0_map[v.split(":",1)[1]] - x1_map[u.split(":",1)[1]])
            if cost < best_cost:
                best_cost = cost
                best_perm0, best_perm1 = perm0, perm1
        
    return list(best_perm0), list(best_perm1)


def optimise_higher_layers(prev_order, curr_order, spacing, G, i):
    """For each layer > 1, test ALL permutations of that layer's nodes and choose the ordering that minimises the total weighted horizontal
    edge length between that layer and the previous layer"""
    
    prev_x = compute_x_positions(prev_order, spacing)

    # Collect edges that connect prev layer to this layer
    inter_edges = []
    for u, v, data in G.edges(data=True):
        lu = G.nodes[u]['layer']
        lv = G.nodes[v]['layer']
        if {lu, lv} == {i-1, i}:
            weight = data.get('weight', 1)
            if lu == i-1:
                prev_name = u.split(":", 1)[1]
                curr_name = v.split(":", 1)[1]
            else:
                prev_name = v.split(":", 1)[1]
                curr_name = u.split(":", 1)[1]
            inter_edges.append((prev_name, curr_name, weight))

    # Test all permutations of curr layer
    best_cost = float("inf")
    best_perm = curr_order

    for perm in itertools.permutations(curr_order):
        curr_x = compute_x_positions(perm, spacing)
        cost = 0
        for p, c, w in inter_edges:
            cost += w * abs(curr_x[c] - prev_x[p])
        if cost < best_cost:
            best_cost = cost
            best_perm = perm
            
    return best_perm


def max_layer_intersections(list_clusters):
    """
    Computes for each pair of consecutive layers the maximum intersection between the games in two vertices connected by an edge
    This will be used for weighting the edges when building the graph
    """
    max_intersections = []

    for i in range(len(list_clusters) - 1):
        dict_i = list_clusters[i]
        dict_next = list_clusters[i + 1]

        # Convert values to sets once
        sets_i = [set(v) for v in dict_i.values()]
        sets_next = [set(v) for v in dict_next.values()]

        max_intersection = 0

        for s1 in sets_i:
            for s2 in sets_next:
                intersection_size = len(s1 & s2)
                if intersection_size > max_intersection:
                    max_intersection = intersection_size

        max_intersections.append(max_intersection)

    return max_intersections



def build_graph(list_clusters, mapper_algorithm_object):
    
    G = nx.Graph()

    # --------------------
    # Build nodes
    # --------------------
    for i, cluster_dict in enumerate(list_clusters):
        for cluster_name, titles in cluster_dict.items():
            node_id = f"{i}:{cluster_name}"
            G.add_node(node_id, layer=i, titles=set(titles), size=len(titles))

    # --------------------
    # Build normalized edges (only between i and i+1)
    # --------------------
    
    max_intersections = max_layer_intersections(list_clusters)
    
    nodes_by_layer = {}
    for node_id, data in G.nodes(data=True):
        nodes_by_layer.setdefault(data["layer"], []).append((node_id, data))

    for i in range(len(list_clusters) - 1):

        for nodeA, dataA in nodes_by_layer[i]:
            for nodeB, dataB in nodes_by_layer[i + 1]:

                shared_size = len(dataA["titles"] & dataB["titles"])

                if shared_size > 0:
                    weight = shared_size / max_intersections[i]
                    G.add_edge(nodeA, nodeB, weight=weight)

    return G

def compute_position_from_order(layer_order, spacing):
    pos = {}
    for i, order in layer_order.items():
        n = len(order)
        for j, name in enumerate(order):
            node_id = f"{i}:{name}"
            x = (j - n/2) * spacing
            y = i                     # vertical separation
            pos[node_id] = (x, y)
            
    return pos


def compute_list_cluster(mapper_algorithm_object):
    """Transform the dict of clusters into a list that will be used in plot_mapper"""
    
    list_clusters = [] # initialise the list
    
    for index_level in mapper_algorithm_object.games_level.keys():
        list_clusters.append(mapper_algorithm_object.dict_level_to_cluster[index_level])
        
    return list_clusters


def layout_minimise_crossings(
    mapper_algorithm_object,
    spacing=2.0
    ):
    """
    Build layered cluster graph.
    Assumes each layer has a few nodes, hopefully not more than 7 ,so permutations are manageable.
    Minimise the total weighted horizontal edge between layers
    """
    
    list_clusters = compute_list_cluster(mapper_algorithm_object)
    
    G = build_graph(list_clusters, mapper_algorithm_object)
    
    # --------------------
    # Initialize layer orders
    # --------------------
    layer_order = {}
    for i, cluster_dict in enumerate(list_clusters):
        layer_order[i] = list(cluster_dict.keys())
        
    
    # Set the best ordering for the first two layers
    layer_order[0], layer_order[1] = optimise_order_two_first_layers(list_clusters, spacing, G)


    # --------------------
    # Optimize each layer > 1
    # --------------------
    L = len(list_clusters)
    for i in range(2, L):
        prev_order = layer_order[i - 1]
        curr_order = layer_order[i]
        
        best_perm = optimise_higher_layers(prev_order, curr_order, spacing, G, i)        

        layer_order[i] = list(best_perm)

    # --------------------
    # Compute final positions
    # --------------------
    pos = compute_position_from_order(layer_order, spacing)
    
    return G, pos


############ Compute graph drawing

def weight_to_gray(w, min_w, max_w):
    if max_w == min_w:
        t = 0.5
    else:
        t = (w - min_w) / (max_w - min_w)

    # Light gray (255) -> medium gray (100)
    gray = int(255 - t * (255 - 100))

    return f"rgba({gray},{gray},{gray},0.6)"


def kpi_x_pos(G, pos):
    """Outputs the x-axis position of where to write the kpi value of each level"""
    
    xs = [pos[n][0] for n in G.nodes]
    x_left = min(xs)
    x_right = max(xs)
    
    x_label = x_left - 0.07 * (x_right - x_left)  # spacing to the left
    
    return x_label

def get_kpi_list(mapper_algorithm_object):
    """transforms the dict of kpi values into a list"""
    
    return list(mapper_algorithm_object.games_level.keys())
        
  
    
def top_5_by_reviewCount(df, titles) -> list:
    """
    Returns the top 5 titles from the list based on the highest reviewCount in the dataframe.

    Parameters:
    - df: pd.DataFrame with columns 'name' and 'reviewCount' (float)
    - titles: list of strings to filter from df['name']

    Returns:
    - List of up to 5 strings with highest reviewCount
    """
    # Filter the dataframe to include only the titles in the list
    filtered_df = df[df['name'].isin(titles)]
    
    # Sort by reviewCount descending and take top 5
    top5 = filtered_df.sort_values(by='reviewCount', ascending=False).head(5)
    
    # Return the names as a list
    return top5['name'].tolist()



def plotly_drawing(G, pos, kpi_x, list_kpi_to_show, gdco_reference, save_as_pdf = False):
    edge_traces = []
    
    # Determine weight range for normalization
    weights = [data.get("weight", 1) for _, _, data in G.edges(data=True)]
    min_w, max_w = min(weights), max(weights)

    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
    
        w = data.get("weight", 1)
    
        edge_traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode='lines',
                line=dict(
                    width=25* w,
                    color=weight_to_gray(w, min_w, max_w)
                ),
                hoverinfo='none'
            )
        )
    
    # -----------------------------
    # Build node traces
    # -----------------------------
    node_x = []
    node_y = []
    node_text = []       # what appears on hover
    node_labels = []     # what appears next to nodes (cluster names)
    node_marker_size = []  # proportional to area
    
    for node, data in G.nodes(data=True):
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
    
        # Label (cluster name only)
        cluster_name = node.split(":", 1)[1]
        node_labels.append(cluster_name)
    
        # Hover text: first 5 titles
        titles = top_5_by_reviewCount(gdco_reference, list(data['titles']))
        preview = "<br>".join(titles[:5])
        if len(titles) > 5:
            preview += "<br>..."
    
        node_text.append(f"<b>{cluster_name}</b><br><br>{preview}")
    
        # Plotly marker.size expects diameter-like values, not area, so convert:
        area = 10 * data['size']
        radius = (area)**0.5  
        node_marker_size.append(radius)
    
    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode='markers+text',
        text=node_labels,
        textposition='top center',
        hovertext=node_text,
        hoverinfo='text',
        textfont=dict(
        size=18,
        family="Arial",
        color="black"
        ),
        marker=dict(
            size=node_marker_size,
            color='lightblue',
            opacity=1.0, 
            line=dict(width=1, color='darkgray')
        )
    )
    

    
    fig = go.Figure(data=edge_traces + [node_trace])
    
    for index_level, kpi_value in enumerate(list_kpi_to_show):
        year = int(kpi_value)
        interval_name = f"({year}-{year+1})" if year != 2025 else "(2025)"
        
        fig.add_annotation(
        x=kpi_x,
        y=index_level,
        text=interval_name,
        showarrow=False,
        xanchor="right",
        yanchor="middle",
        font=dict(size=18),
        align="right"
        )
        
        
    fig.update_layout(
        showlegend=False,
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        width=1750,    # width in pixels
        height=1200,    # height in pixels
    )
    

    
    fig.show(renderer="browser")
    
    if save_as_pdf:
        fig.write_image("results/mapper_graph_paper.pdf")
    
      
    
    
    
def plot_clusters(mapper_algorithm_object):
    
    mapper_algorithm_object._check_all_levels_are_clustered()
    
    G, pos = layout_minimise_crossings(mapper_algorithm_object)
    kpi_x = kpi_x_pos(G, pos)
    list_kpi_to_show = get_kpi_list(mapper_algorithm_object)
    
    plotly_drawing(G, pos, kpi_x, list_kpi_to_show, mapper_algorithm_object.mapper_prepared_object.gdco_reference)