Using the Azure DocumentDB skill, build a Node.js LlamaIndex agent that reads co-purchase order history from Azure DocumentDB, generates product embeddings, stores them in a DiskANN index, and uses agent memory to personalise recommendations per session. The agent should accept a product ID and return the top 5 recommended items with reasoning.

The app should include a script to ingest 20,000 product purchase transactions. The app should include an artistic UI to look like an online retailer's website.

Use a config file for the Azure DocumentDB connection string and display a clear error if the connection string is missing or invalid. Keep the code as simple and readable as possible.

Can you add detailed comments before each method to make code readability by others as easy as possible?
