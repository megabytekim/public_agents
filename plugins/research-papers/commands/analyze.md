---
description: Analyze an academic paper using the cv-paper-analyst agent
---

# Analyze Paper

Invoke the cv-paper-analyst agent to analyze the paper at the specified path or from an arXiv link.

## Usage

The user will provide one of the following:
- A file path to a PDF (e.g., `/Users/newyork/Downloads/paper.pdf`)
- An arXiv paper URL (e.g., `https://arxiv.org/abs/2103.03230`)
- A paper title to search for (e.g., "Barlow Twins")

## Process

1. Verify the current date
2. Extract paper information
3. Perform systematic analysis following the template
4. Search for related research and implementations
5. Create practical applicability assessment
6. Generate both markdown and HTML reports in the results/ directory

Delegate to the cv-paper-analyst agent with the paper information.
