# FDA Drug Approvals MCP Server

A Model Context Protocol (MCP) server that provides access to FDA drug safety data through the openFDA API. This server enables AI assistants to search adverse event reports, drug labeling information, and recall data to support drug safety analysis and research.

## Features

### 🔧 Tools
- **search_drug_events**: Query FDA adverse event reports (FAERS database) for specific drugs
- **get_drug_label_info**: Retrieve official drug labeling information including indications, warnings, and dosage
- **search_drug_recalls**: Search FDA enforcement reports for drug recalls and safety alerts

### 📊 Resources
- **Recent Drug Adverse Events**: Latest adverse event reports from the FDA
- **Popular Drug Labels**: Labeling information for commonly searched medications
- **Recent Drug Recalls**: Current drug recalls and enforcement actions

### 💬 Prompts
- **analyze_drug_safety**: Generate comprehensive safety analysis for a specific drug
- **drug_comparison**: Compare safety profiles across multiple medications

## Installation

### Prerequisites
- Python 3.8+
- Required packages: `httpx`, `mcp`

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/drug-approval-mcp.git
cd drug-approval-mcp
```

2. Install dependencies:
```bash
pip install httpx mcp
```

3. Run the server:
```bash
python fda_mcp_server.py
```

## Usage

### As an MCP Server

The server implements the Model Context Protocol and can be integrated with MCP-compatible AI assistants. Configure your MCP client to connect to this server for FDA data access.

### Direct Testing

Run the test script to verify functionality:
```bash
python test_fda_mcp_server.py
```

### Tool Examples

#### Search Drug Events
```python
# Search for adverse events related to aspirin
{
  "tool": "search_drug_events",
  "arguments": {
    "drug_name": "aspirin",
    "limit": 10,
    "date_range": "20240101_to_20241231"
  }
}
```

#### Get Drug Label Information
```python
# Retrieve labeling information for metformin
{
  "tool": "get_drug_label_info", 
  "arguments": {
    "drug_name": "metformin",
    "limit": 5
  }
}
```

#### Search Drug Recalls
```python
# Find Class I recalls for a specific drug
{
  "tool": "search_drug_recalls",
  "arguments": {
    "drug_name": "lisinopril",
    "classification": "Class I",
    "limit": 10
  }
}
```

## API Endpoints Used

This server interfaces with the following FDA openFDA API endpoints:

- **Drug Adverse Events**: `https://api.fda.gov/drug/event.json`
- **Drug Labeling**: `https://api.fda.gov/drug/label.json`  
- **Drug Enforcement Reports**: `https://api.fda.gov/drug/enforcement.json`

## Data Sources

All data is sourced from the FDA's openFDA API, which provides access to:
- **FAERS (FDA Adverse Event Reporting System)**: Post-market drug safety surveillance
- **SPL (Structured Product Labeling)**: Official drug labeling information
- **Recall Enterprise System (RES)**: FDA enforcement and recall actions

## Response Format

### Drug Events Response
```json
{
  "total_results": 150,
  "events": [
    {
      "report_id": "12345678",
      "receive_date": "20241015",
      "serious": "1",
      "patient_age": "65",
      "patient_sex": "F",
      "reactions": ["Nausea", "Dizziness"],
      "drugs": [
        {
          "name": "ASPIRIN",
          "indication": "Pain relief"
        }
      ]
    }
  ]
}
```

### Drug Label Response
```json
{
  "total_results": 5,
  "labels": [
    {
      "brand_names": ["Tylenol"],
      "generic_names": ["acetaminophen"],
      "manufacturer": ["Johnson & Johnson"],
      "indications_and_usage": ["Pain relief and fever reduction"],
      "warnings": ["Liver damage warning"],
      "adverse_reactions": ["Nausea", "Rash"]
    }
  ]
}
```

### Recall Response
```json
{
  "total_results": 3,
  "recalls": [
    {
      "recall_number": "D-1234-2024",
      "product_description": "Drug name and strength",
      "reason_for_recall": "Contamination",
      "classification": "Class II",
      "status": "Ongoing",
      "recall_initiation_date": "20241001",
      "firm_name": "Manufacturer Name"
    }
  ]
}
```

## Configuration

### Logging
Set the log level using command line arguments:
```bash
python fda_mcp_server.py --log-level DEBUG
```

### Rate Limiting
The FDA API has usage limits. The server respects these by:
- Limiting result sets to reasonable sizes
- Implementing proper error handling for rate limit responses
- Using async/await for efficient request handling

## Error Handling

The server includes comprehensive error handling for:
- Invalid drug names or search parameters
- FDA API rate limiting and downtime
- Network connectivity issues
- Malformed API responses

## Development

### Project Structure
```
drug-approval-mcp/
├── fda_mcp_server.py      # Main MCP server implementation
├── test_fda_mcp_server.py # Test script for validation
├── README.md              # This documentation
├── LICENSE                # MIT License
└── .gitignore            # Git ignore file
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Submit a pull request

### Testing

Run the test suite:
```bash
python test_fda_mcp_server.py
```

## Legal and Compliance

### Data Usage
- All data is publicly available through the FDA's openFDA API
- Data should be used for informational and research purposes
- Not intended as a substitute for professional medical advice

### Disclaimers
- FDA adverse event reports are not verified for medical or scientific accuracy
- The existence of a report does not establish causation between a drug and adverse event
- Always consult healthcare professionals for medical decisions

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the [FDA openFDA documentation](https://open.fda.gov/apis/)
2. Review the error logs for debugging information
3. Submit issues through the repository's issue tracker

## Changelog

### v1.0.0
- Initial release with core MCP server functionality
- Support for adverse events, drug labels, and recalls
- Comprehensive error handling and logging
- Pre-built prompts for common analysis tasks


TO-DO NOTE: Additional data source will come from: https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm