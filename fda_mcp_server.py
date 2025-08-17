#!/usr/bin/env python3
"""
FDA Drug Approvals MCP Server

This MCP server provides access to FDA drug approval data through the openFDA API.
It demonstrates core MCP concepts including tools, resources, and prompts.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urlencode

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.models import InitializationOptions
from mcp.types import (
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
    Resource,
    TextContent,
    Tool,
    ListPromptsResult,
    GetPromptResult,
    Prompt,
    PromptMessage,
    PromptArgument,
    ServerCapabilities
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fda-mcp-server")

# FDA openFDA API base URL
FDA_BASE_URL = "https://api.fda.gov/drug/event.json"
FDA_DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"
FDA_ENFORCEMENT_URL = "https://api.fda.gov/drug/enforcement.json"

class FDAMCPServer:
    def __init__(self):
        self.server = Server("fda-drug-approvals")
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up all MCP handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available FDA data tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="search_drug_events",
                        description="Search FDA adverse event reports for drugs",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "drug_name": {
                                    "type": "string",
                                    "description": "Name of the drug to search for"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results (1-1000)",
                                    "minimum": 1,
                                    "maximum": 1000,
                                    "default": 10
                                },
                                "date_range": {
                                    "type": "string",
                                    "description": "Date range in format YYYYMMDD_to_YYYYMMDD",
                                    "pattern": r"^\d{8}_to_\d{8}$"
                                }
                            },
                            "required": ["drug_name"]
                        }
                    ),
                    Tool(
                        name="get_drug_label_info",
                        description="Get drug labeling information from FDA",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "drug_name": {
                                    "type": "string",
                                    "description": "Name of the drug to get label information for"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results",
                                    "minimum": 1,
                                    "maximum": 100,
                                    "default": 5
                                }
                            },
                            "required": ["drug_name"]
                        }
                    ),
                    Tool(
                        name="search_drug_recalls",
                        description="Search FDA drug enforcement/recall reports",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "drug_name": {
                                    "type": "string",
                                    "description": "Name of the drug to search recalls for"
                                },
                                "classification": {
                                    "type": "string",
                                    "description": "Recall classification (Class I, Class II, Class III)",
                                    "enum": ["Class I", "Class II", "Class III"]
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of results",
                                    "minimum": 1,
                                    "maximum": 100,
                                    "default": 10
                                }
                            },
                            "required": ["drug_name"]
                        }
                    )
                ]
            )

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "search_drug_events":
                    return await self._search_drug_events(arguments)
                elif name == "get_drug_label_info":
                    return await self._get_drug_label_info(arguments)
                elif name == "search_drug_recalls":
                    return await self._search_drug_recalls(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")],
                    isError=True
                )

        @self.server.list_resources()
        async def handle_list_resources() -> ListResourcesResult:
            """List available FDA resources"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="fda://drug-events/recent",
                        name="Recent Drug Adverse Events",
                        description="Recent adverse event reports from FDA",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="fda://drug-labels/popular",
                        name="Popular Drug Labels",
                        description="Labeling information for commonly searched drugs",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="fda://recalls/recent",
                        name="Recent Drug Recalls",
                        description="Recent drug recalls and enforcement actions",
                        mimeType="application/json"
                    )
                ]
            )

        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> ReadResourceResult:
            """Read FDA resources"""
            try:
                if uri == "fda://drug-events/recent":
                    data = await self._get_recent_drug_events()
                elif uri == "fda://drug-labels/popular":
                    data = await self._get_popular_drug_labels()
                elif uri == "fda://recalls/recent":
                    data = await self._get_recent_recalls()
                else:
                    raise ValueError(f"Unknown resource URI: {uri}")
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(data, indent=2)
                        )
                    ]
                )
            except Exception as e:
                logger.error(f"Error reading resource {uri}: {e}")
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Error reading resource: {str(e)}"
                        )
                    ]
                )

        @self.server.list_prompts()
        async def handle_list_prompts() -> ListPromptsResult:
            """List available prompts"""
            return ListPromptsResult(
                prompts=[
                    Prompt(
                        name="analyze_drug_safety",
                        description="Analyze drug safety data from FDA reports",
                        arguments=[
                            PromptArgument(
                                name="drug_name",
                                description="Name of the drug to analyze",
                                required=True
                            ),
                            PromptArgument(
                                name="focus_area",
                                description="Specific safety aspect to focus on (side_effects, recalls, interactions)",
                                required=False
                            )
                        ]
                    ),
                    Prompt(
                        name="drug_comparison",
                        description="Compare safety profiles of multiple drugs",
                        arguments=[
                            PromptArgument(
                                name="drug_list",
                                description="Comma-separated list of drugs to compare",
                                required=True
                            )
                        ]
                    )
                ]
            )

        @self.server.get_prompt()
        async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
            """Get prompt content"""
            try:
                if name == "analyze_drug_safety":
                    return await self._get_safety_analysis_prompt(arguments)
                elif name == "drug_comparison":
                    return await self._get_drug_comparison_prompt(arguments)
                else:
                    raise ValueError(f"Unknown prompt: {name}")
            except Exception as e:
                logger.error(f"Error getting prompt {name}: {e}")
                return GetPromptResult(
                    description="Error getting prompt",
                    messages=[
                        PromptMessage(
                            role="user",
                            content=TextContent(
                                type="text",
                                text=f"Error: {str(e)}"
                            )
                        )
                    ]
                )

    async def _search_drug_events(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for drug adverse events"""
        drug_name = arguments["drug_name"]
        limit = arguments.get("limit", 10)
        date_range = arguments.get("date_range")
        
        # Build search query
        search_query = f'patient.drug.medicinalproduct:"{drug_name}"'
        
        params = {
            "search": search_query,
            "limit": min(limit, 100)  # FDA API limit
        }
        
        if date_range:
            params["search"] += f' AND receivedate:[{date_range.replace("_to_", " TO ")}]'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(FDA_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        # Process results
        events = data.get("results", [])
        processed_events = []
        
        for event in events[:limit]:
            processed_event = {
                "report_id": event.get("safetyreportid", "Unknown"),
                "receive_date": event.get("receivedate", "Unknown"),
                "serious": event.get("serious", "Unknown"),
                "patient_age": event.get("patient", {}).get("patientonsetage", "Unknown"),
                "patient_sex": event.get("patient", {}).get("patientsex", "Unknown"),
                "reactions": [
                    reaction.get("reactionmeddrapt", "Unknown") 
                    for reaction in event.get("patient", {}).get("reaction", [])
                ],
                "drugs": [
                    {
                        "name": drug.get("medicinalproduct", "Unknown"),
                        "indication": drug.get("drugindication", "Unknown")
                    }
                    for drug in event.get("patient", {}).get("drug", [])
                ]
            }
            processed_events.append(processed_event)
        
        result = {
            "total_results": data.get("meta", {}).get("results", {}).get("total", 0),
            "events": processed_events
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=json.dumps(result, indent=2)
            )]
        )

    async def _get_drug_label_info(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Get drug labeling information"""
        drug_name = arguments["drug_name"]
        limit = arguments.get("limit", 5)
        
        params = {
            "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
            "limit": min(limit, 50)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(FDA_DRUG_LABEL_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        labels = data.get("results", [])
        processed_labels = []
        
        for label in labels[:limit]:
            openfda = label.get("openfda", {})
            processed_label = {
                "brand_names": openfda.get("brand_name", []),
                "generic_names": openfda.get("generic_name", []),
                "manufacturer": openfda.get("manufacturer_name", []),
                "substance_names": openfda.get("substance_name", []),
                "product_type": openfda.get("product_type", []),
                "route": openfda.get("route", []),
                "indications_and_usage": label.get("indications_and_usage", ["Not available"]),
                "warnings": label.get("warnings", ["Not available"]),
                "adverse_reactions": label.get("adverse_reactions", ["Not available"]),
                "dosage_and_administration": label.get("dosage_and_administration", ["Not available"])
            }
            processed_labels.append(processed_label)
        
        result = {
            "total_results": data.get("meta", {}).get("results", {}).get("total", 0),
            "labels": processed_labels
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        )

    async def _search_drug_recalls(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Search for drug recalls/enforcement actions"""
        drug_name = arguments["drug_name"]
        classification = arguments.get("classification")
        limit = arguments.get("limit", 10)
        
        search_parts = [f'product_description:"{drug_name}"']
        if classification:
            search_parts.append(f'classification:"{classification}"')
        
        params = {
            "search": " AND ".join(search_parts),
            "limit": min(limit, 100)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(FDA_ENFORCEMENT_URL, params=params)
            response.raise_for_status()
            data = response.json()
        
        recalls = data.get("results", [])
        processed_recalls = []
        
        for recall in recalls[:limit]:
            processed_recall = {
                "recall_number": recall.get("recall_number", "Unknown"),
                "product_description": recall.get("product_description", "Unknown"),
                "reason_for_recall": recall.get("reason_for_recall", "Unknown"),
                "classification": recall.get("classification", "Unknown"),
                "status": recall.get("status", "Unknown"),
                "recall_initiation_date": recall.get("recall_initiation_date", "Unknown"),
                "firm_name": recall.get("recalling_firm", "Unknown"),
                "distribution_pattern": recall.get("distribution_pattern", "Unknown")
            }
            processed_recalls.append(processed_recall)
        
        result = {
            "total_results": data.get("meta", {}).get("results", {}).get("total", 0),
            "recalls": processed_recalls
        }
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        )

    async def _get_recent_drug_events(self) -> Dict[str, Any]:
        """Get recent drug adverse events"""
        # Get events from the last 30 days
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        date_range = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
        
        params = {
            "search": f"receivedate:[{date_range.replace('_to_', ' TO ')}]",
            "limit": 20
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(FDA_BASE_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def _get_popular_drug_labels(self) -> Dict[str, Any]:
        """Get labels for popular drugs"""
        popular_drugs = ["aspirin", "ibuprofen", "acetaminophen", "metformin", "lisinopril"]
        
        all_labels = []
        async with httpx.AsyncClient() as client:
            for drug in popular_drugs[:3]:  # Limit to avoid rate limiting
                try:
                    params = {
                        "search": f'openfda.brand_name:"{drug}" OR openfda.generic_name:"{drug}"',
                        "limit": 1
                    }
                    response = await client.get(FDA_DRUG_LABEL_URL, params=params)
                    response.raise_for_status()
                    data = response.json()
                    if data.get("results"):
                        all_labels.extend(data["results"])
                except Exception as e:
                    logger.warning(f"Error fetching data for {drug}: {e}")
        
        return {"results": all_labels}

    async def _get_recent_recalls(self) -> Dict[str, Any]:
        """Get recent drug recalls"""
        params = {
            "search": "product_type:Drugs",
            "limit": 20,
            "sort": "recall_initiation_date:desc"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(FDA_ENFORCEMENT_URL, params=params)
            response.raise_for_status()
            return response.json()

    async def _get_safety_analysis_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """Generate a safety analysis prompt"""
        drug_name = arguments["drug_name"]
        focus_area = arguments.get("focus_area", "general safety")
        
        prompt_text = f"""
Please analyze the safety profile of {drug_name} focusing on {focus_area}.

Use the FDA MCP server tools to gather comprehensive data:

1. Search for adverse event reports for {drug_name}
2. Get drug labeling information for {drug_name}
3. Check for any recalls or enforcement actions for {drug_name}

Based on this data, provide:
- Summary of reported adverse events and their frequency
- Analysis of warnings and precautions from labeling
- Any recall history and reasons
- Risk-benefit assessment
- Recommendations for monitoring

Please ensure your analysis is evidence-based and cite specific FDA data sources.
"""
        
        return GetPromptResult(
            description=f"Safety analysis prompt for {drug_name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text.strip())
                )
            ]
        )

    async def _get_drug_comparison_prompt(self, arguments: Dict[str, str]) -> GetPromptResult:
        """Generate a drug comparison prompt"""
        drug_list = arguments["drug_list"]
        drugs = [drug.strip() for drug in drug_list.split(",")]
        
        prompt_text = f"""
Please compare the safety profiles of the following drugs: {', '.join(drugs)}

For each drug, use the FDA MCP server tools to gather:
1. Adverse event data
2. Drug labeling information
3. Recall history

Create a comparative analysis including:
- Side effect profiles comparison
- Relative safety rankings
- Different risk factors for each drug
- Contraindications and warnings comparison
- Historical recall patterns

Present the comparison in a clear, structured format that helps understand the relative risks and benefits of each medication.
"""
        
        return GetPromptResult(
            description=f"Comparative analysis prompt for: {', '.join(drugs)}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text.strip())
                )
            ]
        )

    async def run(self):
        """Run the MCP server using stdio transport"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="fda-drug-approvals",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools={},
                        resources={},
                        prompts={}
                    )
                )
            )

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FDA Drug Approvals MCP Server")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Set logging level")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    # Create and run server
    async def run_server():
        server = FDAMCPServer()
        await server.run()
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()