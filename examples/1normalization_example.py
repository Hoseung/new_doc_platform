from litepub_norm import normalize_file
from litepub_norm.serialize import serialize

# Normalize a markdown file
ast = normalize_file("./data/golden_minimal.md", 
                     "./data/registry.json")

# Serialize to JSON
json_output = serialize(ast, indent=2)

# Or save directly
from litepub_norm.serialize import serialize_to_file
serialize_to_file(ast, "./report.normalized.json")