# APS Model Derivatives Assistant

Experimental chatbot for querying design data in [Autodesk Construction Cloud](https://construction.autodesk.com/) using custom [LangChain](https://www.langchain.com) agents and [Autodesk Platform Services](https://aps.autodesk.com) ([Model Derivatives API](https://aps.autodesk.com/en/docs/model-derivative/v2/developers_guide/overview/)).

![Thumbnail](thumbnail.png)

## How does it work?

For any design selected in the frontend, the application extracts its various properties using the [Model Derivatives API](https://aps.autodesk.com/en/docs/model-derivative/v2/developers_guide/overview/), and caches the data in a local [sqlite](https://www.sqlite.org/) database. Then, the application uses a [LangGraph agent](https://python.langchain.com/docs/how_to/migrate_agent/) with built-in tools for querying the database based on user prompts.

## Usage

Login with your Autodesk credentials, select one of your design files in ACC, and try some of the prompts below:

> what are the top 5 elements with the largest area?

> give me the list of IDs of all wall elements

> what is the average height of doors?

> what is the sum of volumes of all floors?

## Development

### Prerequisites

- [APS application](https://aps.autodesk.com/en/docs/oauth/v2/tutorials/create-app/) of the _Desktop, Mobile, Single-Page App_ type
- [OpenAI API key](https://platform.openai.com/docs/quickstart/create-and-export-an-api-key)
- [Python 3.x](https://www.python.org/downloads/)

### Setup

- Clone the repository
- Initialize and activate a virtual environment: `python3 -m venv .venv && source .venv/bin/activate`
- Install Python dependencies: `pip install -r requirements.txt`
- Update [static/config.js](static/config.js) with your APS client ID and callback URL
- Set the following environment variables:
  - `OPENAI_API_KEY` - your OpenAI API key
- Run the dev server: `python server.py`
- Open http://localhost:8000 in the browser