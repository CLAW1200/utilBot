# Take users.csv and construct a graph of users and mutuals from servers they are in

import csv
import json
import graphviz
import networkx as nx
import os
os.environ['PATH'] = r'C:/Program Files (x86)/Graphviz/bin;' + os.environ['PATH']


def create_json_from_csv(csv_file):
    """
    Take the csv file, get all the usernames with userIDs and guilds with guildIDs, and create a json file with the data
    """
    with open(csv_file, "r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        data = {}
        for row in reader:
            # Go to row "ID" and get the value
            userID = row["ID"]
            # Get the associated username and discriminator
            username = row["Username"]
            discriminator = row["Discriminator"]

            # Now fetch the guilds with their IDs. Guilds are separated by a new line and so are IDs
            guilds = row["Guilds"].split("\n")
            guildIDs = row["Guild IDs"].split("\n")

            # Now we have all the data we need, let's create the json file
            # First, let's create a dictionary for the user
            user = {
                "username": username,
                "discriminator": discriminator,
                "guilds": {}
            }

            # Now let's create a dictionary for each guild
            for guild, guildID in zip(guilds, guildIDs):
                user["guilds"][guild] = guildID

            # Now let's add the user to the data dictionary
            data[userID] = user

    # Now let's write the data to a json file
            
    with open("graphData.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=4)

def create_graph_data_from_json(json_file):
    with open(json_file, "r", encoding="utf-8") as json_file:
        data = json.load(json_file)
        graph = {}
        guilds = {}

        for user in data:
            for guild in data[user]["guilds"].values():
                if guild not in guilds:
                    guilds[guild] = [user]
                else:
                    guilds[guild].append(user)

        for user in data:
            mutuals = []
            for guild in data[user]["guilds"].values():
                mutuals.extend(guilds[guild])
            mutuals = list(set(mutuals))  # remove duplicates
            mutuals.remove(user)  # remove the user from their own mutuals
            graph[user] = mutuals

    print (f"Total number of users: {len(graph)}")
    with open("graph.json", "w", encoding="utf-8") as json_file:
        json.dump(graph, json_file, indent=4)

# Take the graph.json data and create a graph
def create_graph_from_json(json_file):
    with open(json_file, "r", encoding="utf-8") as json_file:
        graph = json.load(json_file)
        G = nx.Graph()
        for user in graph:
            G.add_node(user)
            for mutual in graph[user]:
                G.add_edge(user, mutual)

    nx.write_graphml(G, "graph.graphml")


def draw_graphml_file(graphml_file):

    # Create a Graphviz object
    dot = graphviz.Digraph()

    # Read the GraphML file and add nodes and edges to the graph
    with open(graphml_file, 'r') as file:
        # Read the GraphML content
        graphml_content = file.read()
        
        # Add the GraphML content to the Graphviz object
        dot.graph_attr['rankdir'] = 'LR'  # Optional: Set the direction of the graph (left to right)
        dot.node_attr['shape'] = 'circle'  # Optional: Set the shape of the nodes
        
        # Add the content to the graph
        dot.body.append(graphml_content)

    # Render the graph to a file or display it
    output_file = "path/to/output/file.png"  # Path to the output file (e.g., PNG, PDF)
    dot.render(output_file, format='png', view=True)  # Render the graph to a PNG file and display it




if __name__ == "__main__":
    draw_graphml_file("graph.graphml")