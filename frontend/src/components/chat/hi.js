import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

export default function TRNAVisualizer() {
    const svgRef = useRef(null);
    const sequence = "GCGGAUUUAGCUCAGUUGGGAGAGCGCCAGACUGAAGAUCUGGAGGUCCUGUGUUCGAUCCACAGAAUUCGCACCA";

    useEffect(() => {
        const svg = d3.select(svgRef.current);
        const width = 525;
        const height = 550;
        
        // Clear any previous content
        svg.selectAll("*").remove();

        // Create nucleotide nodes
        const nucleotides = sequence.split('').map((base, i) => ({
            id: i + 1,
            base,
            x: 0,
            y: 0,
            color: base === 'A' ? '#ff7f7f' :
                   base === 'U' ? '#7f7fff' :
                   base === 'G' ? '#7fff7f' :
                   base === 'C' ? '#ffff7f' : '#cccccc'
        }));

        // Define base pairs
        const basePairs = [
            [0, 72], [1, 71], [2, 70], [3, 69], [4, 68], [5, 67], [6, 66],
            [10, 25], [11, 24], [12, 23], [13, 22],
            [27, 43], [28, 42], [29, 41], [30, 40], [31, 39],
            [49, 65], [50, 64], [51, 63], [52, 62], [53, 61]
        ];

        // Position nodes according to Sprinzl diagram
        const positions = {
            // Acceptor stem (vertical at top)
            ...Array(7).fill().reduce((acc, _, i) => ({
                ...acc,
                [i]: { x: 250, y: 43 + (i * 25) }
            }), {}),
            
            // D-arm and loop
            ...Array(16).fill().reduce((acc, _, i) => ({
                ...acc,
                [i + 7]: {
                    x: 206 - (i * 20),
                    y: i < 5 ? 262 : 
                       i < 10 ? 262 - ((i-4) * 20) :
                       262 + ((i-9) * 20)
                }
            }), {}),
            
            // Anticodon stem and loop
            ...Array(17).fill().reduce((acc, _, i) => ({
                ...acc,
                [i + 23]: {
                    x: 236,
                    y: 317 + (i * 25)
                }
            }), {}),
            
            // T-arm and loop
            ...Array(17).fill().reduce((acc, _, i) => ({
                ...acc,
                [i + 40]: {
                    x: 319 + (i * 20),
                    y: i < 5 ? 261 :
                       i < 10 ? 261 - ((i-4) * 20) :
                       261 + ((i-9) * 20)
                }
            }), {}),
            
            // Complete acceptor stem
            ...Array(7).fill().reduce((acc, _, i) => ({
                ...acc,
                [i + 66]: { x: 302, y: 43 + (i * 25) }
            }), {})
        };

        // Apply positions to nucleotides
        nucleotides.forEach((n, i) => {
            n.x = positions[i].x;
            n.y = positions[i].y;
        });

        // Draw backbone connections
        const line = d3.line()
            .x(d => d.x)
            .y(d => d.y)
            .curve(d3.curveBasis);

        svg.append("path")
            .datum(nucleotides)
            .attr("fill", "none")
            .attr("stroke", "#999")
            .attr("stroke-width", 1)
            .attr("d", line);

        // Draw base pair connections
        basePairs.forEach(([i, j]) => {
            svg.append("line")
                .attr("x1", nucleotides[i].x)
                .attr("y1", nucleotides[i].y)
                .attr("x2", nucleotides[j].x)
                .attr("y2", nucleotides[j].y)
                .attr("stroke", "#666")
                .attr("stroke-width", 1)
                .attr("stroke-dasharray", "3,3");
        });

        // Draw nucleotides
        const nodes = svg.selectAll("g")
            .data(nucleotides)
            .enter()
            .append("g")
            .attr("transform", d => `translate(${d.x},${d.y})`);

        nodes.append("circle")
            .attr("r", 13)
            .attr("fill", d => d.color)
            .attr("stroke", "#333");

        nodes.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "0.3em")
            .attr("fill", "#000")
            .style("font-size", "15px")
            .text(d => d.base);

        // Add position labels
        nodes.append("text")
            .attr("text-anchor", "middle")
            .attr("dy", "-1.2em")
            .attr("fill", "#666")
            .style("font-size", "10px")
            .text(d => d.id);

    }, []);

    return (
        <div className="w-full h-full flex items-center justify-center bg-white">
            <svg 
                ref={svgRef} 
                width="525" 
                height="550" 
                className="max-w-full max-h-full"
            />
        </div>
    );
}