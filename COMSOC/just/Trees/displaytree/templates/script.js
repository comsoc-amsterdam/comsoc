var container = document.getElementById('mynetwork');

    var data = {
      nodes: nodes,
      edges: edges
    };

    var options = {
      edges: {
        font: {
          color: '#333333',
          background: '#BBBBBB'
        }
      },
      layout: {
        hierarchical: {
          direction: 'UD',
          levelSeparation: 300,
          sortMethod: 'directed'
        },
      },
      physics: {
        hierarchicalRepulsion: {
          nodeDistance: 300,
        },
      },
    };

    var network = new vis.Network(container, data, options);
